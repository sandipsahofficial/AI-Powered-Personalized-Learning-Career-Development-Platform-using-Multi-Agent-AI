import uuid
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.profiling import (
    DocumentSection,
    ExtractedSkillItem,
    SkillEvidence,
    ProfilePreviewResponse
)
from app.services.skill_normalizer import SkillNormalizer, SKILL_ALIASES
from app.services.proficiency_estimator import ProficiencyEstimator
from app.core.llm_client import ollama_client

logger = logging.getLogger(__name__)

PROFILER_SYSTEM_PROMPT = """You are the Senior Profiler Agent for an AI-Powered Learning and Career Development Platform.
Your task is to analyze the learner's resume or profile text and extract evidence-based skills.

CRITICAL RULES:
1. Extract REAL skills demonstrated or declared in the document. Do not invent or hallucinate skills.
2. For each skill, identify the specific evidence from the text:
   - Evidence Type must be one of:
     * "PROJECT_DEMONSTRATED": Built or implemented in a project.
     * "CERTIFICATION_SUPPORTED": Has an official certificate or license.
     * "EXPERIENCE_INFERRED": Used in a job, internship, or professional role.
     * "EXPLICITLY_DECLARED": Listed only in a skills list without project details.
3. Return a JSON object with this EXACT structure:
{
  "skills": [
    {
      "name": "Python",
      "category": "Programming Languages",
      "original_phrase": "Python 3.10",
      "evidence_type": "PROJECT_DEMONSTRATED",
      "source_section": "Projects",
      "evidence_description": "Built an asynchronous web API with background workers."
    }
  ],
  "candidate_headline": "Backend Engineer / Python Developer",
  "summary": "Demonstrates experience in Python backend development and cloud tools."
}
"""


class ProfilerAgent:
    @classmethod
    async def extract_skills(
        cls,
        user_id: uuid.UUID,
        sections: List[DocumentSection],
        full_text: str,
        db: Optional[AsyncSession] = None,
        target_role: Optional[str] = None
    ) -> ProfilePreviewResponse:
        """
        Executes end-to-end profiling: LLM inference -> Normalization -> Proficiency estimation -> Preview.
        """
        # Prepare sanitized prompt content
        prompt_sections_text = "\n\n".join(
            f"=== SECTION: {s.title} ===\n{s.content}" for s in sections
        )
        if not prompt_sections_text.strip():
            prompt_sections_text = full_text[:4000]

        user_prompt = f"""Analyze the following candidate resume document:

<resume_content>
{prompt_sections_text[:6000]}
</resume_content>

Extract all technical and professional skills with evidence following the JSON instructions."""

        # Call Ollama
        json_output, model_used, is_fallback = await ollama_client.generate_structured_json(
            prompt=user_prompt,
            system_prompt=PROFILER_SYSTEM_PROMPT,
            timeout=25.0,
            retries=1
        )

        extracted_raw_skills = []
        doc_summary = None

        if not is_fallback and json_output and "skills" in json_output and isinstance(json_output["skills"], list):
            doc_summary = {
                "headline": json_output.get("candidate_headline", "Learner"),
                "summary": json_output.get("summary", "")
            }
            for item in json_output["skills"]:
                if isinstance(item, dict) and "name" in item:
                    extracted_raw_skills.append({
                        "name": str(item["name"]),
                        "original_phrase": str(item.get("original_phrase", item["name"])),
                        "evidence_type": str(item.get("evidence_type", "EXPLICITLY_DECLARED")),
                        "source_section": str(item.get("source_section", "General")),
                        "evidence_description": str(item.get("evidence_description", "Extracted from resume"))
                    })
        else:
            # Deterministic Fallback Heuristic
            is_fallback = True
            model_used = "deterministic_heuristic_parser"
            extracted_raw_skills = cls._deterministic_extraction(sections, full_text)
            doc_summary = {
                "headline": "Profile Analysis (Deterministic)",
                "summary": f"Extracted {len(extracted_raw_skills)} skills using rule-based pattern matching."
            }

        # Normalize and Estimate Proficiency
        final_skills_dict: Dict[str, ExtractedSkillItem] = {}

        for raw_item in extracted_raw_skills:
            norm_result = await SkillNormalizer.normalize_phrase(raw_item["name"], db=db)
            canonical = norm_result.canonical_name
            cat = norm_result.category

            evidence_obj = SkillEvidence(
                evidence_type=raw_item.get("evidence_type", "EXPLICITLY_DECLARED"),
                source_section=raw_item.get("source_section", "General"),
                original_phrase=raw_item.get("original_phrase", raw_item["name"]),
                description=raw_item.get("evidence_description", "Found in document"),
                confidence_score=norm_result.confidence_score
            )

            if canonical in final_skills_dict:
                # Corroborate: Add additional evidence
                final_skills_dict[canonical].evidence.append(evidence_obj)
            else:
                final_skills_dict[canonical] = ExtractedSkillItem(
                    canonical_name=canonical,
                    category=cat,
                    original_phrase=raw_item.get("original_phrase", raw_item["name"]),
                    normalization_method=norm_result.match_type,
                    evidence=[evidence_obj]
                )

        # Calculate evidence-based proficiency for each unique skill
        final_skill_list: List[ExtractedSkillItem] = []
        categories_breakdown: Dict[str, int] = {}

        for canonical, item in final_skills_dict.items():
            level, status, confidence, reasoning = ProficiencyEstimator.estimate_proficiency(
                canonical_name=canonical,
                evidence_list=item.evidence
            )
            item.proficiency_level = level
            item.proficiency_status = status
            item.confidence_score = confidence
            if reasoning:
                item.user_notes = f"AI Estimate: {reasoning}"

            final_skill_list.append(item)
            categories_breakdown[item.category] = categories_breakdown.get(item.category, 0) + 1

        # Sort: Highest confidence & proficiency first
        final_skill_list.sort(key=lambda s: (s.proficiency_level or 0, s.confidence_score), reverse=True)

        return ProfilePreviewResponse(
            user_id=user_id,
            extracted_skills=final_skill_list,
            total_skills_count=len(final_skill_list),
            categories_breakdown=categories_breakdown,
            ai_model_used=model_used,
            is_fallback=is_fallback,
            extraction_timestamp=datetime.now(timezone.utc),
            document_summary=doc_summary
        )

    @classmethod
    def _deterministic_extraction(
        cls,
        sections: List[DocumentSection],
        full_text: str
    ) -> List[Dict[str, Any]]:
        """
        High-precision deterministic regex & section matching fallback when LLM is unavailable.
        """
        found_skills: List[Dict[str, Any]] = []
        seen_aliases = set()

        for sec in sections:
            sec_title = sec.title
            content = sec.content

            # Determine baseline evidence type based on section
            if sec_title == "Projects":
                ev_type = "PROJECT_DEMONSTRATED"
            elif sec_title == "Certifications":
                ev_type = "CERTIFICATION_SUPPORTED"
            elif sec_title == "Experience":
                ev_type = "EXPERIENCE_INFERRED"
            else:
                ev_type = "EXPLICITLY_DECLARED"

            # Scan text for known aliases using word boundaries
            for alias, (canonical, category) in SKILL_ALIASES.items():
                # Avoid single letter false positives unless in Technical Skills
                if len(alias) <= 1 and sec_title != "Technical Skills":
                    continue

                pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches and (canonical, sec_title) not in seen_aliases:
                    seen_aliases.add((canonical, sec_title))
                    # Extract surrounding sentence snippet as evidence description
                    match = matches[0]
                    start = max(0, match.start() - 40)
                    end = min(len(content), match.end() + 60)
                    snippet = content[start:end].replace("\n", " ").strip()

                    found_skills.append({
                        "name": canonical,
                        "original_phrase": match.group(0),
                        "evidence_type": ev_type,
                        "source_section": sec_title,
                        "evidence_description": f"...{snippet}..."
                    })

        return found_skills

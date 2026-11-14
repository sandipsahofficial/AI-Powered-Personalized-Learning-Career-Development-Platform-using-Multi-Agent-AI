import re
from typing import Tuple, Optional, List
from app.schemas.profiling import SkillEvidence

# Indicators of advanced/expert depth
HIGH_COMPLEXITY_PATTERNS = [
    r"production", r"scale", r"high[- ]traffic", r"distributed", r"architecture",
    r"optimized", r"lead", r"senior", r"architect", r"benchmark", r"concurrency",
    r"microservice", r"pipeline", r"orchestrat", r"refactor", r"internals", r"kernel"
]

# Indicators of intermediate depth
INTERMEDIATE_PATTERNS = [
    r"developed", r"implemented", r"built", r"created", r"integrated",
    r"api", r"database", r"rest", r"full[- ]stack", r"tested", r"deployed"
]

# Indicators of foundational/beginner exposure
BEGINNER_PATTERNS = [
    r"familiar", r"basic", r"exposure", r"coursework", r"academic", r"learned", r"introductory"
]

# Time duration patterns
EXPERIENCE_YEAR_PATTERN = r"(\d+)\+?\s*(?:year|yr)s?"


class ProficiencyEstimator:
    @classmethod
    def estimate_proficiency(
        cls,
        canonical_name: str,
        evidence_list: List[SkillEvidence]
    ) -> Tuple[Optional[int], str, float, str]:
        """
        Calculates evidence-based proficiency level (1 to 5), status, confidence score, and explanation.
        Returns:
            (proficiency_level, proficiency_status, confidence_score, reasoning)
        """
        if not evidence_list:
            return (
                None,
                "INSUFFICIENT_EVIDENCE",
                0.20,
                f"No descriptive evidence found for {canonical_name}. Listed without project or experience context."
            )

        evidence_types = {e.evidence_type for e in evidence_list}
        combined_text = " ".join(f"{e.source_section}: {e.description}" for e in evidence_list).lower()
        
        # 1. Check for insufficient context (single explicit declaration with <= 15 chars)
        if evidence_types == {"EXPLICITLY_DECLARED"} and len(combined_text) < 40:
            return (
                None,
                "INSUFFICIENT_EVIDENCE",
                0.35,
                f"{canonical_name} is only declared in a skills list without project, work, or certification details to substantiate depth."
            )

        # 2. Extract years of experience if mentioned
        years_found = [int(m) for m in re.findall(EXPERIENCE_YEAR_PATTERN, combined_text)]
        max_years = max(years_found) if years_found else 0

        # 3. Check complexity keywords
        high_matches = sum(1 for p in HIGH_COMPLEXITY_PATTERNS if re.search(p, combined_text))
        int_matches = sum(1 for p in INTERMEDIATE_PATTERNS if re.search(p, combined_text))
        beg_matches = sum(1 for p in BEGINNER_PATTERNS if re.search(p, combined_text))

        # 4. Certification Presence
        has_cert = "CERTIFICATION_SUPPORTED" in evidence_types
        has_proj = "PROJECT_DEMONSTRATED" in evidence_types
        has_exp = "EXPERIENCE_INFERRED" in evidence_types

        # Decision Matrix:
        # Tier 5: Expert (Lead/architect role, 5+ years, or production architecture with certifications)
        if (max_years >= 5 and high_matches >= 2) or (high_matches >= 3 and has_exp and (has_cert or has_proj)):
            level = 5
            confidence = 0.90
            reasoning = (
                f"Demonstrated deep expertise in {canonical_name} with {max_years if max_years else 'extensive'} years "
                f"experience and multiple production-scale architectural implementations."
            )
            status = "ESTIMATED"

        # Tier 4: Advanced (3+ years, or strong project implementations with production/optimization focus)
        elif (max_years >= 3) or (high_matches >= 1 and (has_proj or has_exp)) or (has_cert and has_proj):
            level = 4
            confidence = 0.85
            reasoning = (
                f"Advanced competency in {canonical_name} supported by "
                f"{'certified credentials and ' if has_cert else ''}practical project implementations demonstrating production depth."
            )
            status = "ESTIMATED"

        # Tier 3: Intermediate (Multiple project implementations or 1-2 years experience)
        elif (has_proj and int_matches >= 1) or has_cert or (has_exp and int_matches >= 1) or (len(evidence_list) >= 2 and int_matches >= 2):
            level = 3
            confidence = 0.80
            reasoning = (
                f"Solid practical working knowledge in {canonical_name} with concrete hands-on project implementations."
            )
            status = "ESTIMATED"

        # Tier 2: Basic (Academic projects or introductory implementations)
        elif has_proj or int_matches >= 1 or beg_matches == 0:
            level = 2
            confidence = 0.65
            reasoning = (
                f"Basic working foundation in {canonical_name}. Found in project descriptions with foundational usage."
            )
            status = "ESTIMATED"

        # Tier 1: Beginner
        else:
            level = 1
            confidence = 0.50
            reasoning = (
                f"Introductory familiarity in {canonical_name}. Evidence reflects coursework or preliminary exposure."
            )
            status = "ESTIMATED"

        return (level, status, confidence, reasoning)

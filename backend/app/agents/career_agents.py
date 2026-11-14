import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.llm_client import ollama_client

logger = logging.getLogger(__name__)


class GapAnalyzerAgent:
    """Specialized agent that evaluates candidate readiness against target career benchmarks."""
    
    @staticmethod
    def analyze_gaps(role_title: str, matching: List[str], weak: List[str], missing: List[str], match_pct: float) -> Dict[str, Any]:
        verdict = (
            "READY_FOR_HIRE" if match_pct >= 85.0 else
            "NEAR_READY" if match_pct >= 65.0 else
            "IN_DEVELOPMENT" if match_pct >= 40.0 else
            "BEGINNER_PATHWAY"
        )
        recommendations = []
        if missing:
            recommendations.append(f"Focus primarily on unmastered mandatory technologies: {', '.join(missing[:3])}.")
        if weak:
            recommendations.append(f"Elevate competency in foundational tools currently at lower proficiency: {', '.join(weak[:3])}.")
        if not recommendations:
            recommendations.append("Solid skill alignment achieved. Concentrate on system design, portfolio projects, and mock interviews.")

        return {
            "agent": "GapAnalyzerAgent",
            "role_title": role_title,
            "readiness_verdict": verdict,
            "match_percentage": match_pct,
            "primary_actions": recommendations
        }


class AssessmentEvaluatorAgent:
    """Specialized agent that diagnoses quiz results, highlighting misconceptions and remediation steps."""

    @staticmethod
    def evaluate(score: float, max_score: float, milestone_title: str, passed: bool) -> Dict[str, Any]:
        pct = round((score / max_score * 100.0) if max_score > 0 else 0.0, 1)
        if passed:
            feedback = (
                f"Evaluation: PASSED ({pct}%). The learner demonstrated strong comprehension of "
                f"concepts in '{milestone_title}'. Recommended to proceed to subsequent architectural phases."
            )
        else:
            feedback = (
                f"Evaluation: REMEDIAL REQUIRED ({pct}% vs 70% threshold). Misconceptions detected in core principles "
                f"of '{milestone_title}'. The adaptive scheduler has assigned revision exercises."
            )
        return {
            "agent": "AssessmentEvaluatorAgent",
            "percentage": pct,
            "passed": passed,
            "feedback": feedback
        }


class AdaptiveReplannerAgent:
    """Agent that dynamically modifies roadmap status and injects remedial work when learning friction is observed."""

    @staticmethod
    def trigger_replan(milestone_title: str, reason: str = "ASSESSMENT_FAILURE") -> Dict[str, Any]:
        return {
            "agent": "AdaptiveReplannerAgent",
            "trigger": reason,
            "action": "FLAGGED_FOR_REMEDIATION",
            "message": f"Adaptive intervention triggered for '{milestone_title}'. Roadmap paused at current milestone until conceptual mastery is verified."
        }


class CareerCoachAgent:
    """AI Mentor that provides contextual guidance drawing from actual student skills, target career, and milestones."""

    COACH_SYSTEM_PROMPT = """You are an expert, encouraging, and highly technical Senior AI Career Mentor.
You are mentoring a student on an AI-powered personalized learning platform.
You have access to their real data:
- Current Confirmed Skills
- Selected Target Career Goal
- Match / Readiness Percentage
- Current Roadmap Milestone Status
- Recent Assessment Scores

GUIDELINES:
1. Provide concrete, actionable, and encouraging technical advice.
2. Directly reference their actual target career, skills, and current milestone.
3. If they have weak or missing skills, explain why those matter in production.
4. Keep responses structured, concise, and easy to read (use markdown bullet points).
5. Never hallucinate fake enterprise experience; guide them towards building high-signal portfolio deliverables.
"""

    @classmethod
    async def get_mentor_response(
        cls,
        user_message: str,
        target_role: Optional[str],
        confirmed_skills: List[str],
        match_pct: Optional[float],
        current_milestone: Optional[str],
        milestone_status: Optional[str],
        recent_quiz_score: Optional[float]
    ) -> str:
        context_block = f"""
STUDENT CONTEXT:
- Target Career: {target_role or 'Not specified yet'}
- Confirmed Skills: {', '.join(confirmed_skills) if confirmed_skills else 'None confirmed yet'}
- Career Readiness Score: {f'{match_pct}%' if match_pct is not None else 'Not computed'}
- Current Milestone: {current_milestone or 'Phase 1: Core Foundations'} ({milestone_status or 'IN_PROGRESS'})
- Recent Assessment Score: {f'{recent_quiz_score}%' if recent_quiz_score is not None else 'None taken yet'}
"""
        prompt = f"{context_block}\nSTUDENT QUESTION:\n{user_message}\n\nMENTOR RESPONSE:"

        # Try LLM generation via Ollama
        response_text, model_used, is_fallback = await ollama_client.generate_text(
            prompt=prompt,
            system_prompt=cls.COACH_SYSTEM_PROMPT,
            timeout=15.0
        )

        if not is_fallback and response_text:
            return response_text

        # Context-aware deterministic fallback
        return cls._generate_deterministic_advice(
            user_message=user_message,
            target_role=target_role,
            confirmed_skills=confirmed_skills,
            match_pct=match_pct,
            current_milestone=current_milestone,
            milestone_status=milestone_status,
            recent_quiz_score=recent_quiz_score
        )

    @classmethod
    def _generate_deterministic_advice(
        cls,
        user_message: str,
        target_role: Optional[str],
        confirmed_skills: List[str],
        match_pct: Optional[float],
        current_milestone: Optional[str],
        milestone_status: Optional[str],
        recent_quiz_score: Optional[float]
    ) -> str:
        msg_lower = user_message.lower()
        role = target_role or "Full Stack Developer"
        skills_str = ", ".join(confirmed_skills[:4]) if confirmed_skills else "JavaScript and Python"
        pct_str = f"{match_pct}%" if match_pct is not None else "45%"

        if "next" in msg_lower or "focus" in msg_lower or "what should i learn" in msg_lower:
            return f"""### Recommended Next Steps for {role}

Based on your current readiness score of **{pct_str}** and confirmed skills (**{skills_str}**):

1. **Current Milestone Priority**: Focus on **{current_milestone or 'Phase 1: Core Web Foundations'}**.
2. **Key Competency Target**: Complete the milestone deliverable to demonstrate end-to-end hands-on proficiency.
3. **Milestone Validation**: Once you finish reading the curated documentation, take the milestone quiz to unlock your next development phase.

Keep your commit log clean and practice writing tests alongside your code!"""

        elif "interview" in msg_lower or "hire" in msg_lower or "job" in msg_lower:
            return f"""### Interview Preparation Strategy for {role}

To advance from your current **{pct_str}** match to hiring readiness (>85%):

1. **Showcase Measurable Projects**: Replace generic tutorials with a full-stack production application that incorporates authentication, relational data persistence, and Docker deployment.
2. **Master the Fundamentals**: Interviewers for {role} will grill you on asynchronous execution, data indexing, and state management.
3. **System Design & API Contracts**: Practice designing clean REST/JSON contracts and normalized schemas.

You already have a solid base in **{skills_str}**—building on that will set you apart!"""

        elif "remedial" in msg_lower or "failed" in msg_lower or "weak" in msg_lower or (recent_quiz_score and recent_quiz_score < 70):
            return f"""### Remedial Guidance & Skill Reinforcement

Don't be discouraged by an assessment score of **{f'{recent_quiz_score}%' if recent_quiz_score else 'below 70%'}**. Finding gaps early is how real mastery is built!

1. **Review Official Documentation**: Re-read the curated MDN and official documentation linked in your milestone card.
2. **Build a Minimal Reproduction**: If you stumbled on state or async concepts, write a 20-line standalone script to inspect the behavior hands-on.
3. **Retake with Confidence**: When you feel solid, retake the assessment. Passing with 70%+ immediately clears your remedial status and unlocks the next phase!"""

        else:
            return f"""### Career Mentorship Note

Welcome! As your AI Career Mentor, here is an executive summary of where you stand:

- **Target Career Path**: **{role}**
- **Current Alignment**: **{pct_str}** readiness based on your confirmed skills ({skills_str}).
- **Active Focus**: **{current_milestone or 'Phase 1: Core Foundations'}** (Status: `{milestone_status or 'IN_PROGRESS'}`).

Feel free to ask me about specific syntax challenges, interview preparation, or how to tackle your current roadmap deliverables!"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.ai import AIMentorConversation
from app.models.career import UserCareerGoal, CareerRole, CareerMatchingResult
from app.models.skill import UserSkill, Skill
from app.models.learning import LearningRoadmap, RoadmapMilestone
from app.models.assessment import AssessmentResult
from app.agents.career_agents import CareerCoachAgent
from app.schemas.mentor import MentorChatResponse, MentorConversationHistoryResponse

logger = logging.getLogger(__name__)


class MentorService:
    @staticmethod
    async def chat(user_id: uuid.UUID, message: str, db: AsyncSession) -> MentorChatResponse:
        # 1. Fetch User's confirmed skills
        skills_res = await db.execute(
            select(Skill.name)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
        )
        confirmed_skills = [r[0] for r in skills_res.all()]

        # 2. Fetch Active Career Goal
        goal_res = await db.execute(
            select(UserCareerGoal, CareerRole)
            .join(CareerRole, UserCareerGoal.career_role_id == CareerRole.id)
            .where(UserCareerGoal.user_id == user_id, UserCareerGoal.status == "ACTIVE")
            .order_by(UserCareerGoal.created_at.desc())
        )
        goal_row = goal_res.first()
        target_role = goal_row[1].title if goal_row else None
        role_id = goal_row[0].career_role_id if goal_row else None

        # 3. Match %
        match_pct = None
        if role_id:
            match_res = await db.execute(
                select(CareerMatchingResult.match_percentage)
                .where(
                    CareerMatchingResult.user_id == user_id,
                    CareerMatchingResult.career_role_id == role_id
                )
                .order_by(CareerMatchingResult.computed_at.desc())
            )
            match_pct = match_res.scalars().first()

        # 4. Active Milestone
        roadmap_res = await db.execute(
            select(LearningRoadmap)
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
            .order_by(LearningRoadmap.created_at.desc())
        )
        roadmap = roadmap_res.scalars().first()

        curr_milestone_title = None
        curr_milestone_status = None
        if roadmap:
            ms_res = await db.execute(
                select(RoadmapMilestone)
                .where(
                    RoadmapMilestone.roadmap_id == roadmap.id,
                    RoadmapMilestone.status.in_(["IN_PROGRESS", "REMEDIAL"])
                )
                .order_by(RoadmapMilestone.order_index)
            )
            active_ms = ms_res.first()
            if active_ms:
                curr_milestone_title = active_ms[0].title
                curr_milestone_status = active_ms[0].status

        # 5. Recent Assessment
        recent_assess_res = await db.execute(
            select(AssessmentResult.percentage)
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentResult.evaluated_at.desc())
        )
        recent_score = recent_assess_res.scalars().first()

        # 6. Generate Response via CareerCoachAgent
        reply = await CareerCoachAgent.get_mentor_response(
            user_message=message,
            target_role=target_role,
            confirmed_skills=confirmed_skills,
            match_pct=match_pct,
            current_milestone=curr_milestone_title,
            milestone_status=curr_milestone_status,
            recent_quiz_score=recent_score
        )

        now_utc = datetime.now(timezone.utc)

        # 7. Persist in AIMentorConversation
        conv_res = await db.execute(
            select(AIMentorConversation)
            .where(AIMentorConversation.user_id == user_id)
            .order_by(AIMentorConversation.created_at.desc())
        )
        conv = conv_res.scalars().first()

        history = conv.messages_history if conv and isinstance(conv.messages_history, list) else []
        history.append({
            "role": "user",
            "content": message,
            "timestamp": now_utc.isoformat()
        })
        history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": now_utc.isoformat()
        })

        if conv:
            conv.messages_history = history
            conv.last_interaction_at = now_utc
        else:
            conv = AIMentorConversation(
                user_id=user_id,
                session_title=f"Mentorship with {target_role or 'AI Coach'}",
                messages_history=history,
                last_interaction_at=now_utc
            )
            db.add(conv)

        await db.commit()

        return MentorChatResponse(
            reply=reply,
            timestamp=now_utc,
            active_role=target_role,
            readiness_percentage=match_pct,
            current_milestone=curr_milestone_title
        )

    @staticmethod
    async def get_conversation_history(user_id: uuid.UUID, db: AsyncSession) -> Optional[MentorConversationHistoryResponse]:
        conv_res = await db.execute(
            select(AIMentorConversation)
            .where(AIMentorConversation.user_id == user_id)
            .order_by(AIMentorConversation.created_at.desc())
        )
        conv = conv_res.scalars().first()
        if not conv:
            return None

        return MentorConversationHistoryResponse(
            id=conv.id,
            session_title=conv.session_title,
            messages=conv.messages_history or [],
            last_interaction_at=conv.last_interaction_at
        )

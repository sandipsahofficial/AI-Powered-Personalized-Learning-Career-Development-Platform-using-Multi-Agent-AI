import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.career import CareerRole, CareerCategory, CareerSkillRequirement, UserCareerGoal, CareerMatchingResult
from app.models.skill import Skill, UserSkill
from app.core.exceptions import ResourceNotFoundException
from app.schemas.career import (
    CareerRoleSummary,
    CareerRoleDetail,
    CareerSkillRequirementItem,
    SkillGapItem,
    CareerMatchResponse,
    UserCareerGoalResponse
)

logger = logging.getLogger(__name__)


class CareerService:
    @staticmethod
    async def list_roles(db: AsyncSession) -> List[CareerRoleSummary]:
        query = (
            select(CareerRole)
            .options(selectinload(CareerRole.category))
            .order_by(CareerRole.title)
        )
        res = await db.execute(query)
        roles = res.scalars().all()
        
        results = []
        for r in roles:
            results.append(CareerRoleSummary(
                id=r.id,
                title=r.title,
                slug=r.slug,
                category_name=r.category.name if r.category else None,
                industry_demand_level=r.industry_demand_level,
                average_salary_range=r.average_salary_range,
                description=r.description
            ))
        return results

    @staticmethod
    async def get_role(role_id: uuid.UUID, db: AsyncSession) -> CareerRoleDetail:
        query = (
            select(CareerRole)
            .options(
                selectinload(CareerRole.category),
                selectinload(CareerRole.skill_requirements).joinedload(CareerSkillRequirement.career_role)
            )
            .where(CareerRole.id == role_id)
        )
        res = await db.execute(query)
        role = res.scalar_one_or_none()
        if not role:
            raise ResourceNotFoundException(f"Career role with id '{role_id}' not found.")

        # Load requirements with skill names
        req_query = (
            select(CareerSkillRequirement, Skill)
            .join(Skill, CareerSkillRequirement.skill_id == Skill.id)
            .where(CareerSkillRequirement.career_role_id == role_id)
            .order_by(CareerSkillRequirement.importance_weight.desc())
        )
        req_res = await db.execute(req_query)
        req_rows = req_res.all()

        req_items = []
        for req, sk in req_rows:
            req_items.append(CareerSkillRequirementItem(
                skill_id=sk.id,
                skill_name=sk.name,
                required_proficiency=req.required_proficiency,
                importance_weight=req.importance_weight,
                is_mandatory=req.is_mandatory
            ))

        return CareerRoleDetail(
            id=role.id,
            title=role.title,
            slug=role.slug,
            category_name=role.category.name if role.category else None,
            industry_demand_level=role.industry_demand_level,
            average_salary_range=role.average_salary_range,
            description=role.description,
            skill_requirements=req_items
        )

    @staticmethod
    async def match_career(user_id: uuid.UUID, role_id: uuid.UUID, db: AsyncSession) -> CareerMatchResponse:
        # 1. Fetch Career Role
        role_res = await db.execute(
            select(CareerRole)
            .options(selectinload(CareerRole.category))
            .where(CareerRole.id == role_id)
        )
        role = role_res.scalar_one_or_none()
        if not role:
            raise ResourceNotFoundException(f"Career role with id '{role_id}' not found.")

        # 2. Fetch Requirements with Skills
        req_res = await db.execute(
            select(CareerSkillRequirement, Skill)
            .join(Skill, CareerSkillRequirement.skill_id == Skill.id)
            .where(CareerSkillRequirement.career_role_id == role_id)
        )
        req_rows = req_res.all()

        # 3. Fetch User's confirmed skills
        user_skills_res = await db.execute(
            select(UserSkill, Skill)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
        )
        user_skills_map: Dict[str, UserSkill] = {}
        for us, sk in user_skills_res.all():
            user_skills_map[sk.name.lower()] = us
            user_skills_map[str(us.skill_id)] = us

        matching_skills: List[SkillGapItem] = []
        weak_skills: List[SkillGapItem] = []
        missing_skills: List[SkillGapItem] = []

        total_weight = 0.0
        achieved_weight = 0.0

        for req, sk in req_rows:
            weight = req.importance_weight
            total_weight += weight
            req_prof = req.required_proficiency

            # Check if user has skill (by id or normalized name)
            user_skill = user_skills_map.get(str(sk.id)) or user_skills_map.get(sk.name.lower())

            if not user_skill or user_skill.proficiency_level == 0:
                missing_skills.append(SkillGapItem(
                    skill_id=sk.id,
                    skill_name=sk.name,
                    user_proficiency=0,
                    required_proficiency=req_prof,
                    importance_weight=weight,
                    is_mandatory=req.is_mandatory,
                    status="MISSING",
                    gap_level=req_prof
                ))
            elif user_skill.proficiency_level >= req_prof:
                achieved_weight += weight
                matching_skills.append(SkillGapItem(
                    skill_id=sk.id,
                    skill_name=sk.name,
                    user_proficiency=user_skill.proficiency_level,
                    required_proficiency=req_prof,
                    importance_weight=weight,
                    is_mandatory=req.is_mandatory,
                    status="MATCHED",
                    gap_level=0
                ))
            else:
                # Weak skill: partial credit proportional to level
                fraction = user_skill.proficiency_level / float(req_prof)
                achieved_weight += (weight * fraction)
                weak_skills.append(SkillGapItem(
                    skill_id=sk.id,
                    skill_name=sk.name,
                    user_proficiency=user_skill.proficiency_level,
                    required_proficiency=req_prof,
                    importance_weight=weight,
                    is_mandatory=req.is_mandatory,
                    status="WEAK",
                    gap_level=req_prof - user_skill.proficiency_level
                ))

        match_pct = round((achieved_weight / total_weight * 100.0) if total_weight > 0 else 0.0, 1)

        gap_summary = {
            "role_title": role.title,
            "readiness_verdict": (
                "READY_FOR_HIRE" if match_pct >= 85.0 else
                "NEAR_READY" if match_pct >= 65.0 else
                "IN_DEVELOPMENT" if match_pct >= 40.0 else
                "BEGINNER_PATHWAY"
            ),
            "match_percentage": match_pct,
            "matched_count": len(matching_skills),
            "weak_count": len(weak_skills),
            "missing_count": len(missing_skills),
            "mandatory_missing": [m.skill_name for m in missing_skills if m.is_mandatory],
            "key_recommendation": (
                f"Prioritize learning {', '.join([m.skill_name for m in missing_skills if m.is_mandatory][:3])}."
                if [m for m in missing_skills if m.is_mandatory]
                else "Strengthen advanced topics in weak skills to attain interview readiness."
            )
        }

        # Persist or update CareerMatchingResult
        existing_result_res = await db.execute(
            select(CareerMatchingResult).where(
                CareerMatchingResult.user_id == user_id,
                CareerMatchingResult.career_role_id == role_id
            )
        )
        existing_res = existing_result_res.scalar_one_or_none()
        now_utc = datetime.now(timezone.utc)

        if existing_res:
            existing_res.match_percentage = match_pct
            existing_res.gap_summary = gap_summary
            existing_res.computed_at = now_utc
        else:
            new_res = CareerMatchingResult(
                user_id=user_id,
                career_role_id=role_id,
                match_percentage=match_pct,
                gap_summary=gap_summary,
                computed_at=now_utc
            )
            db.add(new_res)

        await db.commit()

        return CareerMatchResponse(
            career_role_id=role.id,
            career_role_title=role.title,
            category_name=role.category.name if role.category else None,
            match_percentage=match_pct,
            matched_skills_count=len(matching_skills),
            weak_skills_count=len(weak_skills),
            missing_skills_count=len(missing_skills),
            total_required_skills=len(req_rows),
            matching_skills=matching_skills,
            weak_skills=weak_skills,
            missing_skills=missing_skills,
            gap_summary=gap_summary,
            computed_at=now_utc
        )

    @staticmethod
    async def set_career_goal(user_id: uuid.UUID, role_id: uuid.UUID, target_date: Optional[datetime], db: AsyncSession) -> UserCareerGoalResponse:
        role_res = await db.execute(select(CareerRole).where(CareerRole.id == role_id))
        role = role_res.scalar_one_or_none()
        if not role:
            raise ResourceNotFoundException(f"Career role with id '{role_id}' not found.")

        # Check existing goal
        goal_res = await db.execute(
            select(UserCareerGoal).where(
                UserCareerGoal.user_id == user_id,
                UserCareerGoal.status == "ACTIVE"
            )
        )
        current_goal = goal_res.scalar_one_or_none()
        now_utc = datetime.now(timezone.utc)

        if current_goal:
            current_goal.career_role_id = role_id
            current_goal.target_completion_date = target_date
            goal = current_goal
        else:
            goal = UserCareerGoal(
                user_id=user_id,
                career_role_id=role_id,
                target_completion_date=target_date,
                status="ACTIVE"
            )
            db.add(goal)

        await db.commit()
        await db.refresh(goal)

        # Get latest match %
        match_res = await db.execute(
            select(CareerMatchingResult.match_percentage)
            .where(
                CareerMatchingResult.user_id == user_id,
                CareerMatchingResult.career_role_id == role_id
            )
        )
        pct = match_res.scalar_one_or_none()

        return UserCareerGoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            career_role_id=goal.career_role_id,
            career_role_title=role.title,
            status=goal.status,
            target_completion_date=goal.target_completion_date,
            match_percentage=pct,
            created_at=goal.created_at
        )

    @staticmethod
    async def get_active_goal(user_id: uuid.UUID, db: AsyncSession) -> Optional[UserCareerGoalResponse]:
        goal_res = await db.execute(
            select(UserCareerGoal)
            .where(UserCareerGoal.user_id == user_id, UserCareerGoal.status == "ACTIVE")
            .order_by(UserCareerGoal.created_at.desc())
        )
        goal = goal_res.scalar_one_or_none()
        if not goal:
            return None

        role_res = await db.execute(select(CareerRole).where(CareerRole.id == goal.career_role_id))
        role = role_res.scalar_one_or_none()

        match_res = await db.execute(
            select(CareerMatchingResult.match_percentage)
            .where(
                CareerMatchingResult.user_id == user_id,
                CareerMatchingResult.career_role_id == goal.career_role_id
            )
        )
        pct = match_res.scalar_one_or_none()

        return UserCareerGoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            career_role_id=goal.career_role_id,
            career_role_title=role.title if role else "Target Role",
            status=goal.status,
            target_completion_date=goal.target_completion_date,
            match_percentage=pct,
            created_at=goal.created_at
        )

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.skill import Skill, SkillCategory, UserSkill
from app.schemas.skill import UserSkillCreateRequest, UserSkillUpdateRequest


class SkillService:
    @staticmethod
    async def list_categories(db: AsyncSession) -> List[SkillCategory]:
        result = await db.execute(select(SkillCategory).order_by(SkillCategory.name))
        return list(result.scalars().all())

    @staticmethod
    async def list_skills(
        db: AsyncSession,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Skill]:
        query = select(Skill).order_by(Skill.name).limit(limit).offset(offset)
        if category_id:
            query = query.where(Skill.category_id == category_id)
        if search:
            query = query.where(Skill.name.ilike(f"%{search}%"))
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_skills(db: AsyncSession, user_id: uuid.UUID) -> List[UserSkill]:
        result = await db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .options(selectinload(UserSkill.skill))
            .order_by(UserSkill.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_user_skill(db: AsyncSession, user_id: uuid.UUID, data: UserSkillCreateRequest) -> UserSkill:
        # Check skill exists
        skill_res = await db.execute(select(Skill).where(Skill.id == data.skill_id))
        skill = skill_res.scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

        # Check existing user skill
        existing = await db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == data.skill_id)
        )
        user_skill = existing.scalar_one_or_none()
        if user_skill:
            user_skill.proficiency_level = data.proficiency_level
            user_skill.updated_at = datetime.now(timezone.utc)
        else:
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=data.skill_id,
                proficiency_level=data.proficiency_level,
                confidence_score=0.50,
                source="SELF_REPORTED"
            )
            db.add(user_skill)

        await db.commit()
        await db.refresh(user_skill)
        # Load skill relation
        user_skill.skill = skill
        return user_skill

    @staticmethod
    async def update_user_skill(db: AsyncSession, user_id: uuid.UUID, skill_id: uuid.UUID, data: UserSkillUpdateRequest) -> UserSkill:
        result = await db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
            .options(selectinload(UserSkill.skill))
        )
        user_skill = result.scalar_one_or_none()
        if not user_skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User skill not found")

        user_skill.proficiency_level = data.proficiency_level
        user_skill.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user_skill)
        return user_skill

    @staticmethod
    async def delete_user_skill(db: AsyncSession, user_id: uuid.UUID, skill_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
        )
        user_skill = result.scalar_one_or_none()
        if not user_skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User skill not found")

        await db.delete(user_skill)
        await db.commit()
        return True

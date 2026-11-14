import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.skill import (
    SkillCategoryResponse,
    SkillResponse,
    UserSkillResponse,
    UserSkillCreateRequest,
    UserSkillUpdateRequest
)
from app.services.skill_service import SkillService

router = APIRouter()


@router.get("/categories", response_model=List[SkillCategoryResponse], summary="List Canonical Skill Categories")
async def list_skill_categories(db: AsyncSession = Depends(get_db)):
    categories = await SkillService.list_categories(db)
    return [SkillCategoryResponse.model_validate(c) for c in categories]


@router.get("", response_model=List[SkillResponse], summary="Search and List Skills Catalog")
async def list_skills(
    category_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    skills = await SkillService.list_skills(db, category_id=category_id, search=search, limit=limit, offset=offset)
    return [SkillResponse.model_validate(s) for s in skills]


@router.get("/me", response_model=List[UserSkillResponse], summary="List Skills of Current Authenticated User")
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_skills = await SkillService.get_user_skills(db, current_user.id)
    return [
        UserSkillResponse(
            id=us.id,
            skill_id=us.skill_id,
            skill_name=us.skill.name if us.skill else "Unknown Skill",
            proficiency_level=us.proficiency_level,
            confidence_score=us.confidence_score,
            is_verified=us.is_verified,
            source=us.source,
            last_assessed_at=us.last_assessed_at
        )
        for us in user_skills
    ]


@router.post("/me", response_model=UserSkillResponse, summary="Add Skill to Current User Profile")
async def add_my_skill(
    data: UserSkillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    us = await SkillService.add_user_skill(db, current_user.id, data)
    return UserSkillResponse(
        id=us.id,
        skill_id=us.skill_id,
        skill_name=us.skill.name if us.skill else "Unknown Skill",
        proficiency_level=us.proficiency_level,
        confidence_score=us.confidence_score,
        is_verified=us.is_verified,
        source=us.source,
        last_assessed_at=us.last_assessed_at
    )


@router.patch("/me/{skill_id}", response_model=UserSkillResponse, summary="Update Current User Skill Proficiency")
async def update_my_skill(
    skill_id: uuid.UUID,
    data: UserSkillUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    us = await SkillService.update_user_skill(db, current_user.id, skill_id, data)
    return UserSkillResponse(
        id=us.id,
        skill_id=us.skill_id,
        skill_name=us.skill.name if us.skill else "Unknown Skill",
        proficiency_level=us.proficiency_level,
        confidence_score=us.confidence_score,
        is_verified=us.is_verified,
        source=us.source,
        last_assessed_at=us.last_assessed_at
    )


@router.delete("/me/{skill_id}", summary="Remove Skill from Current User Profile")
async def delete_my_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await SkillService.delete_user_skill(db, current_user.id, skill_id)
    return {"message": "Skill removed successfully"}

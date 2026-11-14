import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.career_service import CareerService
from app.services.career_seeder import CareerSeeder
from app.schemas.career import (
    CareerRoleSummary,
    CareerRoleDetail,
    CareerMatchResponse,
    SelectCareerGoalRequest,
    UserCareerGoalResponse
)

router = APIRouter()


@router.post("/seed", status_code=status.HTTP_200_OK, summary="Seed Career Roles & Resources")
async def seed_careers(db: AsyncSession = Depends(get_db)):
    """Idempotently seeds career roles, requirements, and free curated resources."""
    await CareerSeeder.seed_career_data(db)
    return {"message": "Career taxonomy and learning resources successfully seeded."}


@router.get("/roles", response_model=List[CareerRoleSummary], summary="List All Career Roles")
async def list_career_roles(db: AsyncSession = Depends(get_db)):
    """Returns all available career paths."""
    return await CareerService.list_roles(db)


@router.get("/roles/{role_id}", response_model=CareerRoleDetail, summary="Get Career Role Details")
async def get_career_role(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns detailed career role information and skill requirements."""
    return await CareerService.get_role(role_id, db)


@router.get("/roles/{role_id}/match", response_model=CareerMatchResponse, summary="Match Skills Against Career Requirements")
async def match_career_role(
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculates readiness %, matching skills, weak skills, and missing skills for the current user."""
    return await CareerService.match_career(current_user.id, role_id, db)


@router.post("/goals", response_model=UserCareerGoalResponse, summary="Select Active Target Career Goal")
async def set_career_goal(
    request: SelectCareerGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sets the user's primary active target career goal."""
    return await CareerService.set_career_goal(current_user.id, request.career_role_id, request.target_completion_date, db)


@router.get("/goals/me", response_model=Optional[UserCareerGoalResponse], summary="Get Current Active Career Goal")
async def get_active_goal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves current user's active career goal."""
    return await CareerService.get_active_goal(current_user.id, db)

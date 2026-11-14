import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.roadmap_service import RoadmapService
from app.schemas.roadmap import (
    LearningRoadmapResponse,
    MilestoneResponse,
    CuratedResourceItem,
    MilestoneStatusUpdateRequest,
    GenerateRoadmapRequest
)

router = APIRouter()


@router.post("/generate", response_model=LearningRoadmapResponse, summary="Generate Personalized Learning Roadmap")
async def generate_roadmap(
    request: GenerateRoadmapRequest,
    force_recreate: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates or retrieves active personalized roadmap mapped to user's skill gaps."""
    return await RoadmapService.generate_or_get_roadmap(
        user_id=current_user.id,
        career_role_id=request.career_role_id,
        db=db,
        force_recreate=force_recreate
    )


@router.get("/active", response_model=Optional[LearningRoadmapResponse], summary="Get Active Learning Roadmap")
async def get_active_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves current user's active learning roadmap with milestones and resources."""
    return await RoadmapService.get_active_roadmap(current_user.id, db)


@router.patch("/milestones/{milestone_id}/status", response_model=LearningRoadmapResponse, summary="Update Milestone Status")
async def update_milestone_status(
    milestone_id: uuid.UUID,
    request: MilestoneStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates a milestone status (e.g., IN_PROGRESS, COMPLETED, REMEDIAL) and updates roadmap progress %."""
    return await RoadmapService.update_milestone_status(
        user_id=current_user.id,
        milestone_id=milestone_id,
        new_status=request.status,
        db=db
    )


@router.get("/resources/recommended", response_model=List[CuratedResourceItem], summary="Get Curated Resource Recommendations")
async def get_recommended_resources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns curated free learning resources mapped to user's missing and weak skills."""
    return await RoadmapService.get_recommended_resources(current_user.id, db)

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.assessment_service import AssessmentService
from app.schemas.assessment import (
    AssessmentDetailResponse,
    AssessmentSubmissionRequest,
    AssessmentResultResponse,
    ProgressSummaryResponse
)

router = APIRouter()


@router.get("/milestones/{milestone_id}", response_model=AssessmentDetailResponse, summary="Get Milestone Assessment Quiz")
async def get_milestone_quiz(
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves or creates assessment quiz for a specific roadmap milestone."""
    return await AssessmentService.get_or_create_milestone_assessment(milestone_id, db)


@router.post("/submit", response_model=AssessmentResultResponse, summary="Submit Assessment Quiz Answers")
async def submit_quiz(
    request: AssessmentSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scores quiz answers, updates milestone status, and triggers adaptive replanning if failed."""
    return await AssessmentService.submit_assessment(current_user.id, request, db)


@router.get("/progress/summary", response_model=ProgressSummaryResponse, summary="Get Learner Progress & Competency Summary")
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Aggregates active career readiness %, roadmap progress %, completed milestones, and assessment history."""
    return await AssessmentService.get_progress_summary(current_user.id, db)

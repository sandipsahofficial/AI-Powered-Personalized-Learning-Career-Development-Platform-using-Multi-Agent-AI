import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.profiling import (
    DocumentUploadResponse,
    ProfilePreviewResponse,
    ExtractedSkillItem,
    ExtractionRequest,
    SkillReviewUpdateRequest,
    SkillNormalizeRequest,
    SkillNormalizeResponse,
    ProfileConfirmRequest,
    ProfileConfirmResponse,
    ProfilingStatusResponse
)
from app.services.profiling_service import ProfilingService
from app.services.skill_normalizer import SkillNormalizer

router = APIRouter()


@router.post(
    "/resume/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Parse Resume Document"
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    content = await file.read()
    return await ProfilingService.process_and_cache_resume(
        user_id=current_user.id,
        filename=file.filename or "uploaded_resume.txt",
        content=content,
        content_type=file.content_type or ""
    )


@router.post(
    "/extract",
    response_model=ProfilePreviewResponse,
    summary="Run AI Profiler Agent Skill Extraction"
)
async def extract_skills(
    data: Optional[ExtractionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    raw_text = data.raw_text if data else None
    use_cached = data.use_cached_resume if data else True
    target_role = data.target_role if data else None

    return await ProfilingService.extract_and_preview(
        user_id=current_user.id,
        raw_text=raw_text,
        use_cached_resume=use_cached,
        target_role=target_role,
        db=db
    )


@router.post(
    "/normalize",
    response_model=SkillNormalizeResponse,
    summary="Normalize Arbitrary Skill Phrases against Taxonomy"
)
async def normalize_skills(
    data: SkillNormalizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    results = await SkillNormalizer.normalize_batch(data.phrases, db=db)
    return SkillNormalizeResponse(results=results)


@router.get(
    "/preview",
    response_model=ProfilePreviewResponse,
    summary="Get Current Extracted Profile Preview"
)
async def get_profile_preview(
    current_user: User = Depends(get_current_user)
):
    preview = await ProfilingService.get_preview(current_user.id)
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profiling preview found. Please upload a resume or extract skills first."
        )
    return preview


@router.get(
    "/skills",
    response_model=List[ExtractedSkillItem],
    summary="List Extracted Skills Awaiting Review"
)
async def list_preview_skills(
    current_user: User = Depends(get_current_user)
):
    preview = await ProfilingService.get_preview(current_user.id)
    if not preview:
        return []
    return preview.extracted_skills


@router.patch(
    "/skills/{skill_id}",
    response_model=ExtractedSkillItem,
    summary="Review and Update an Extracted Skill (Proficiency / Accept / Reject)"
)
async def update_skill_review(
    skill_id: str,
    data: SkillReviewUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    updated = await ProfilingService.update_extracted_skill(
        user_id=current_user.id,
        skill_id=skill_id,
        update_data=data
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted skill with ID '{skill_id}' not found in current preview."
        )
    return updated


@router.post(
    "/confirm",
    response_model=ProfileConfirmResponse,
    summary="Confirm and Persist Approved Skills to User Profile"
)
async def confirm_profile_skills(
    data: ProfileConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ProfilingService.confirm_and_persist_skills(
        user_id=current_user.id,
        confirm_data=data,
        db=db
    )


@router.get(
    "/status",
    response_model=ProfilingStatusResponse,
    summary="Get Profiling Progress and Summary Status"
)
async def get_profiling_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ProfilingService.get_profiling_status(current_user.id, db=db)

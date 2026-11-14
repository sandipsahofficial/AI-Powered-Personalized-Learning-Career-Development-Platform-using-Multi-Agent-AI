import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CuratedResourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    url: str
    resource_type: str
    provider_name: Optional[str] = None
    rating: float
    estimated_minutes: int
    is_free: bool
    content_summary: Optional[str] = None


class MilestoneResourceResponse(BaseModel):
    id: uuid.UUID
    resource: CuratedResourceItem
    display_order: int
    is_mandatory: bool


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phase_number: int
    order_index: int
    title: str
    description: Optional[str] = None
    deliverable_title: Optional[str] = None
    deliverable_criteria: Optional[str] = None
    estimated_hours: int
    status: str  # LOCKED, IN_PROGRESS, REVIEW_PENDING, COMPLETED, REMEDIAL
    is_remedial: bool
    resources: List[CuratedResourceItem] = []
    created_at: datetime


class LearningRoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    career_role_id: uuid.UUID
    career_role_title: str
    title: str
    status: str
    version: int
    total_estimated_hours: int
    progress_percentage: float
    milestones: List[MilestoneResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class MilestoneStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(LOCKED|IN_PROGRESS|REVIEW_PENDING|COMPLETED|REMEDIAL)$")


class GenerateRoadmapRequest(BaseModel):
    career_role_id: uuid.UUID

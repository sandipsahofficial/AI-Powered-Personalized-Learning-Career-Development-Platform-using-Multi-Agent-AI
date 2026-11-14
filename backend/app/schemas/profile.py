import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    user_id: uuid.UUID
    headline: Optional[str] = None
    bio: Optional[str] = None
    target_career_title: Optional[str] = None
    hours_per_week_commitment: int = 10
    preferred_learning_style: str = "BALANCED"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdateRequest(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    target_career_title: Optional[str] = Field(None, max_length=255)
    hours_per_week_commitment: Optional[int] = Field(None, ge=1, le=80)
    preferred_learning_style: Optional[str] = Field(None, max_length=50)
    raw_resume_text: Optional[str] = None

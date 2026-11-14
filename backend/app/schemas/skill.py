import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SkillCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SkillResponse(BaseModel):
    id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    difficulty_level: int = 1

    model_config = {"from_attributes": True}


class UserSkillCreateRequest(BaseModel):
    skill_id: uuid.UUID
    proficiency_level: int = Field(default=1, ge=1, le=4)


class UserSkillUpdateRequest(BaseModel):
    proficiency_level: int = Field(..., ge=1, le=4)


class UserSkillResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    proficiency_level: int
    confidence_score: float
    is_verified: bool
    source: str
    last_assessed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

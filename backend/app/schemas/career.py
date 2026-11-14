import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CareerSkillRequirementItem(BaseModel):
    skill_id: uuid.UUID
    skill_name: str
    required_proficiency: int
    importance_weight: float
    is_mandatory: bool


class CareerRoleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    category_name: Optional[str] = None
    industry_demand_level: str
    average_salary_range: Optional[str] = None
    description: Optional[str] = None


class CareerRoleDetail(CareerRoleSummary):
    skill_requirements: List[CareerSkillRequirementItem] = []


class SkillGapItem(BaseModel):
    skill_id: Optional[uuid.UUID] = None
    skill_name: str
    user_proficiency: int
    required_proficiency: int
    importance_weight: float
    is_mandatory: bool
    status: str  # "MATCHED", "WEAK", "MISSING"
    gap_level: int  # 0 if matched, otherwise required - user


class CareerMatchResponse(BaseModel):
    career_role_id: uuid.UUID
    career_role_title: str
    category_name: Optional[str] = None
    match_percentage: float
    matched_skills_count: int
    weak_skills_count: int
    missing_skills_count: int
    total_required_skills: int
    matching_skills: List[SkillGapItem]
    weak_skills: List[SkillGapItem]
    missing_skills: List[SkillGapItem]
    gap_summary: Dict[str, Any]
    computed_at: datetime


class SelectCareerGoalRequest(BaseModel):
    career_role_id: uuid.UUID
    target_completion_date: Optional[datetime] = None


class UserCareerGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    career_role_id: uuid.UUID
    career_role_title: str
    status: str
    target_completion_date: Optional[datetime] = None
    match_percentage: Optional[float] = None
    created_at: datetime

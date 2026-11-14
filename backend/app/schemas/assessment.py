import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AssessmentOptionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    option_text: str
    # Note: is_correct is NOT returned in student question view, only in result


class AssessmentOptionResultItem(BaseModel):
    id: uuid.UUID
    option_text: str
    is_correct: bool
    explanation: Optional[str] = None


class AssessmentQuestionItem(BaseModel):
    id: uuid.UUID
    question_text: str
    points: float
    order_index: int
    options: List[AssessmentOptionItem]


class AssessmentDetailResponse(BaseModel):
    id: uuid.UUID
    milestone_id: uuid.UUID
    milestone_title: str
    title: str
    passing_score: float
    time_limit_minutes: Optional[int] = 15
    questions: List[AssessmentQuestionItem]


class AnswerSubmissionItem(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class AssessmentSubmissionRequest(BaseModel):
    assessment_id: uuid.UUID
    answers: List[AnswerSubmissionItem]


class AssessmentResultResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment_id: uuid.UUID
    milestone_id: uuid.UUID
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    status: str
    ai_evaluator_feedback: str
    adaptive_action: Optional[str] = None
    evaluated_at: datetime


class ProgressSummaryResponse(BaseModel):
    user_id: uuid.UUID
    target_career_title: Optional[str] = None
    readiness_percentage: float = 0.0
    confirmed_skills_count: int = 0
    active_roadmap_title: Optional[str] = None
    roadmap_progress_percentage: float = 0.0
    completed_milestones_count: int = 0
    total_milestones_count: int = 0
    assessments_taken_count: int = 0
    assessments_passed_count: int = 0
    recent_assessment: Optional[AssessmentResultResponse] = None

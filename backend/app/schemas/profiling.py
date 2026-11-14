import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    title: str
    content: str
    char_count: int


class DocumentUploadResponse(BaseModel):
    filename: str
    file_type: str
    size_bytes: int
    char_count: int
    sections_detected: List[str]
    sections: List[DocumentSection]
    extracted_text_preview: str
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SkillEvidence(BaseModel):
    evidence_type: str = Field(
        ...,
        description="PROJECT_DEMONSTRATED, CERTIFICATION_SUPPORTED, EXPERIENCE_INFERRED, EXPLICITLY_DECLARED, or INSUFFICIENT_EVIDENCE"
    )
    source_section: str = Field(..., description="Section where evidence was found")
    original_phrase: str = Field(..., description="Verbatim or close phrase from the document")
    description: str = Field(..., description="Clear explanation of the evidence context")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)


class ExtractedSkillItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canonical_name: str
    category: str
    original_phrase: str
    proficiency_level: Optional[int] = Field(default=None, ge=1, le=5)  # 1: Beginner, 2: Basic, 3: Intermediate, 4: Advanced, 5: Expert
    proficiency_status: str = Field(
        default="ESTIMATED",
        description="ESTIMATED, INSUFFICIENT_EVIDENCE, USER_CONFIRMED, or USER_OVERRIDDEN"
    )
    confidence_score: float = Field(default=0.75, ge=0.0, le=1.0)
    evidence: List[SkillEvidence] = Field(default_factory=list)
    normalization_method: str = Field(default="EXACT_MATCH")  # EXACT_MATCH, ALIAS_MATCH, SEMANTIC_MATCH, HEURISTIC
    is_confirmed: bool = False
    is_rejected: bool = False
    user_notes: Optional[str] = None


class ExtractionRequest(BaseModel):
    raw_text: Optional[str] = None
    use_cached_resume: bool = True
    target_role: Optional[str] = None


class ProfilePreviewResponse(BaseModel):
    user_id: uuid.UUID
    extracted_skills: List[ExtractedSkillItem]
    total_skills_count: int
    categories_breakdown: Dict[str, int]
    ai_model_used: str
    is_fallback: bool = False
    extraction_timestamp: datetime
    document_summary: Optional[Dict[str, Any]] = None


class SkillReviewUpdateRequest(BaseModel):
    proficiency_level: Optional[int] = Field(default=None, ge=1, le=5)
    is_confirmed: Optional[bool] = None
    is_rejected: Optional[bool] = None
    user_notes: Optional[str] = None


class SkillNormalizeRequest(BaseModel):
    phrases: List[str]


class NormalizedSkillResult(BaseModel):
    original_phrase: str
    canonical_name: str
    category: str
    confidence_score: float
    match_type: str  # EXACT, ALIAS, SEMANTIC, UNMATCHED


class SkillNormalizeResponse(BaseModel):
    results: List[NormalizedSkillResult]


class ProfileConfirmRequest(BaseModel):
    confirmed_skill_ids: Optional[List[str]] = None
    reject_all_unconfirmed: bool = False
    custom_skills: Optional[List[ExtractedSkillItem]] = None


class ProfileConfirmResponse(BaseModel):
    user_id: uuid.UUID
    persisted_count: int
    updated_count: int
    total_skills_in_profile: int
    status: str = "CONFIRMED"
    message: str


class ProfilingStatusResponse(BaseModel):
    has_uploaded_resume: bool
    last_uploaded_filename: Optional[str] = None
    last_extracted_at: Optional[datetime] = None
    total_skills_in_preview: int = 0
    confirmed_skills_count: int = 0
    pending_review_count: int = 0
    total_persisted_skills: int = 0

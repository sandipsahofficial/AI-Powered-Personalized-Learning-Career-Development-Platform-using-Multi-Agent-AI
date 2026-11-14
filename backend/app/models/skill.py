import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, Text, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.models.base import Base, UUIDMixin, TimestampMixin


class SkillCategory(Base, UUIDMixin):
    __tablename__ = "skill_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    skills: Mapped[List["Skill"]] = relationship("Skill", back_populates="category")


class Skill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skills"

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)  # 1 (Beginner) to 4 (Expert)
    skill_embedding = mapped_column(Vector(768), nullable=True)

    category: Mapped[Optional["SkillCategory"]] = relationship("SkillCategory", back_populates="skills")
    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class SkillPrerequisite(Base, UUIDMixin):
    __tablename__ = "skill_prerequisites"
    __table_args__ = (
        UniqueConstraint("skill_id", "prerequisite_skill_id", name="uq_skill_prereq"),
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prerequisite_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dependency_strength: Mapped[str] = mapped_column(String(20), default="MANDATORY")  # 'MANDATORY', 'RECOMMENDED'


class UserSkill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1)  # 1 to 4
    confidence_score: Mapped[float] = mapped_column(Float, default=0.50)  # 0.00 to 1.00
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(50), default="SELF_REPORTED")
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="skills", foreign_keys=[user_id])
    verifier: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by])
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")
    verifications: Mapped[List["SkillVerificationRecord"]] = relationship("SkillVerificationRecord", back_populates="user_skill", cascade="all, delete-orphan")


class SkillAssessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_assessments"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passing_score: Mapped[float] = mapped_column(Float, default=70.0)

    results: Mapped[List["SkillAssessmentResult"]] = relationship("SkillAssessmentResult", back_populates="assessment", cascade="all, delete-orphan")


class SkillAssessmentResult(Base, UUIDMixin):
    __tablename__ = "skill_assessment_results"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    assessment: Mapped["SkillAssessment"] = relationship("SkillAssessment", back_populates="results")


class SkillVerificationRecord(Base, UUIDMixin):
    __tablename__ = "skill_verification_records"

    user_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verifier_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_skill: Mapped["UserSkill"] = relationship("UserSkill", back_populates="verifications")

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, UUIDMixin, TimestampMixin


class CareerCategory(Base, UUIDMixin):
    __tablename__ = "career_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    roles: Mapped[List["CareerRole"]] = relationship("CareerRole", back_populates="category")


class CareerRole(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "career_roles"

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry_demand_level: Mapped[str] = mapped_column(String(20), default="HIGH")
    average_salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    category: Mapped[Optional["CareerCategory"]] = relationship("CareerCategory", back_populates="roles")
    skill_requirements: Mapped[List["CareerSkillRequirement"]] = relationship("CareerSkillRequirement", back_populates="career_role", cascade="all, delete-orphan")
    benchmarks: Mapped[List["CareerBenchmark"]] = relationship("CareerBenchmark", back_populates="career_role", cascade="all, delete-orphan")


class CareerSkillRequirement(Base, UUIDMixin):
    __tablename__ = "career_skill_requirements"
    __table_args__ = (
        UniqueConstraint("career_role_id", "skill_id", name="uq_role_skill"),
    )

    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    required_proficiency: Mapped[int] = mapped_column(Integer, default=2)  # 1 to 4
    importance_weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    career_role: Mapped["CareerRole"] = relationship("CareerRole", back_populates="skill_requirements")


class CareerBenchmark(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "career_benchmarks"

    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    benchmark_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    career_role: Mapped["CareerRole"] = relationship("CareerRole", back_populates="benchmarks")


class UserCareerGoal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_career_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=1)
    target_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")  # ACTIVE, ACHIEVED, ARCHIVED


class CareerMatchingResult(Base, UUIDMixin):
    __tablename__ = "career_matching_results"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    gap_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

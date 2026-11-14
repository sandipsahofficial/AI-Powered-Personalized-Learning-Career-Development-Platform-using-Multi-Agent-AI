import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

from app.models.base import Base, UUIDMixin, TimestampMixin


class ResourceCategory(Base, UUIDMixin):
    __tablename__ = "resource_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resources: Mapped[List["LearningResource"]] = relationship("LearningResource", back_populates="category")


class LearningResource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "learning_resources"

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resource_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'ARTICLE', 'VIDEO', 'DOCUMENTATION', 'GITHUB_REPO'
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    provider_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    content_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_embedding = mapped_column(Vector(768), nullable=True)

    category: Mapped[Optional["ResourceCategory"]] = relationship("ResourceCategory", back_populates="resources")


class LearningRoadmap(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "learning_roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")  # DRAFT, ACTIVE, PAUSED, COMPLETED
    version: Mapped[int] = mapped_column(Integer, default=1)
    total_estimated_hours: Mapped[int] = mapped_column(Integer, default=0)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    milestones: Mapped[List["RoadmapMilestone"]] = relationship("RoadmapMilestone", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapMilestone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roadmap_milestones"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase_number: Mapped[int] = mapped_column(Integer, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliverable_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deliverable_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String(30), default="LOCKED")  # LOCKED, IN_PROGRESS, REVIEW_PENDING, COMPLETED, REMEDIAL
    is_remedial: Mapped[bool] = mapped_column(Boolean, default=False)

    roadmap: Mapped["LearningRoadmap"] = relationship("LearningRoadmap", back_populates="milestones")
    resources: Mapped[List["MilestoneResource"]] = relationship("MilestoneResource", back_populates="milestone", cascade="all, delete-orphan")


class MilestoneResource(Base, UUIDMixin):
    __tablename__ = "milestone_resources"
    __table_args__ = (
        UniqueConstraint("milestone_id", "resource_id", name="uq_milestone_resource"),
    )

    milestone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_milestones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    milestone: Mapped["RoadmapMilestone"] = relationship("RoadmapMilestone", back_populates="resources")


class LearningActivity(Base, UUIDMixin):
    __tablename__ = "learning_activities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_milestones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # READING, QUIZ, CODE_PRACTICE
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearningProgress(Base, UUIDMixin):
    __tablename__ = "learning_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_milestones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CourseCompletionRecord(Base, UUIDMixin):
    __tablename__ = "course_completion_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    certificate_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class LearningHistory(Base, UUIDMixin):
    __tablename__ = "learning_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

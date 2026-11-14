import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, UUIDMixin, TimestampMixin


class Assessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assessments"

    milestone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_milestones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(50), default="QUIZ")  # QUIZ, CODE_SUBMISSION, PROJECT_REVIEW
    passing_score: Mapped[float] = mapped_column(Float, default=70.0)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    questions: Mapped[List["AssessmentQuestion"]] = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")
    attempts: Mapped[List["AssessmentAttempt"]] = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(Base, UUIDMixin):
    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), default="MCQ")  # MCQ, CODE, ESSAY
    points: Mapped[float] = mapped_column(Float, default=1.0)
    order_index: Mapped[int] = mapped_column(Integer, default=1)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="questions")
    options: Mapped[List["AssessmentOption"]] = relationship("AssessmentOption", back_populates="question", cascade="all, delete-orphan")


class AssessmentOption(Base, UUIDMixin):
    __tablename__ = "assessment_options"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    question: Mapped["AssessmentQuestion"] = relationship("AssessmentQuestion", back_populates="options")


class AssessmentAttempt(Base, UUIDMixin):
    __tablename__ = "assessment_attempts"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="IN_PROGRESS")  # IN_PROGRESS, SUBMITTED, GRADED

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="attempts")
    answers: Mapped[List["AssessmentAnswer"]] = relationship("AssessmentAnswer", back_populates="attempt", cascade="all, delete-orphan")
    result: Mapped[Optional["AssessmentResult"]] = relationship("AssessmentResult", back_populates="attempt", uselist=False, cascade="all, delete-orphan")


class AssessmentAnswer(Base, UUIDMixin):
    __tablename__ = "assessment_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_options.id", ondelete="SET NULL"), nullable=True
    )
    submitted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    awarded_points: Mapped[float] = mapped_column(Float, default=0.0)

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="answers")


class AssessmentResult(Base, UUIDMixin):
    __tablename__ = "assessment_results"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ai_evaluator_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="result")

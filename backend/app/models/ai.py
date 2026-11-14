import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, UUIDMixin, TimestampMixin


class AgentExecutionHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_execution_history"

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS")  # SUCCESS, FAILED, RETRYING
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    logs: Mapped[List["AgentExecutionLog"]] = relationship("AgentExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class AgentExecutionLog(Base, UUIDMixin):
    __tablename__ = "agent_execution_logs"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_execution_history.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_level: Mapped[str] = mapped_column(String(20), default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    execution: Mapped["AgentExecutionHistory"] = relationship("AgentExecutionHistory", back_populates="logs")


class AIRecommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SKILL, RESOURCE, CAREER_PATH
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)

    history: Mapped[List["RecommendationHistory"]] = relationship("RecommendationHistory", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationHistory(Base, UUIDMixin):
    __tablename__ = "recommendation_history"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_action: Mapped[str] = mapped_column(String(30), nullable=False)  # VIEWED, ACCEPTED, DISMISSED
    action_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    recommendation: Mapped["AIRecommendation"] = relationship("AIRecommendation", back_populates="history")


class AdaptiveReplanningEvent(Base, UUIDMixin):
    __tablename__ = "adaptive_replanning_events"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_reason: Mapped[str] = mapped_column(String(100), nullable=False)  # ASSESSMENT_FAILURE, USER_REQUEST
    prior_milestone_count: Mapped[int] = mapped_column(Integer, nullable=False)
    new_milestone_count: Mapped[int] = mapped_column(Integer, nullable=False)
    replanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AIMentorConversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_mentor_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_title: Mapped[str] = mapped_column(String(255), default="Career & Learning Mentorship")
    messages_history: Mapped[list] = mapped_column(JSONB, default=list)
    last_interaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

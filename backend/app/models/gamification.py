import uuid
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserGamification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_gamification"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    badges_unlocked: Mapped[list] = mapped_column(JSONB, default=list)


class PointsHistory(Base, UUIDMixin):
    __tablename__ = "points_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    points_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AchievementRecord(Base, UUIDMixin):
    __tablename__ = "achievement_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Notification(Base, UUIDMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), default="SYSTEM")  # SYSTEM, MILESTONE, REMINDER
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserActivityLog(Base, UUIDMixin):
    __tablename__ = "user_activity_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

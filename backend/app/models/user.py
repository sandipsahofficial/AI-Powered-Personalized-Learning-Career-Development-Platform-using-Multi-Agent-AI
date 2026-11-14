import enum
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Text, Integer, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserRoleEnum(str, enum.Enum):
    STUDENT = "STUDENT"
    MENTOR = "MENTOR"
    ORG_ADMIN = "ORG_ADMIN"
    SYS_ADMIN = "SYS_ADMIN"


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    memberships: Mapped[List["OrganizationMembership"]] = relationship("OrganizationMembership", back_populates="organization")


class OrganizationMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organization_memberships"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_in_org: Mapped[str] = mapped_column(String(50), default="MEMBER")

    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(
        SQLEnum(UserRoleEnum, name="user_role_enum"), default=UserRoleEnum.STUDENT, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="users")
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences: Mapped[Optional["UserPreference"]] = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memberships: Mapped[List["OrganizationMembership"]] = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserSkill.user_id")


class UserProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_career_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hours_per_week_commitment: Mapped[int] = mapped_column(Integer, default=10)
    preferred_learning_style: Mapped[str] = mapped_column(String(50), default="BALANCED")
    raw_resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_embedding = mapped_column(Vector(768), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserPreference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    ai_coaching_frequency: Mapped[str] = mapped_column(String(50), default="WEEKLY")

    user: Mapped["User"] = relationship("User", back_populates="preferences")


class UserSession(Base, UUIDMixin):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class RefreshToken(Base, UUIDMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

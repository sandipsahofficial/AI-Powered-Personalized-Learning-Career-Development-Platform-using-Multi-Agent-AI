import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User, UserProfile, UserSession
from app.schemas.profile import UserProfileUpdateRequest


class UserService:
    @staticmethod
    async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> UserProfile:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: uuid.UUID, data: UserProfileUpdateRequest) -> UserProfile:
        profile = await UserService.get_profile(db, user_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)

        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def get_sessions(db: AsyncSession, user_id: uuid.UUID) -> List[UserSession]:
        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke_session(db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        session.is_revoked = True
        await db.commit()
        return True

    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User).where(User.is_deleted == False).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

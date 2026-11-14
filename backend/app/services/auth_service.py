import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_secure_token,
    hash_token,
    revoke_token_jti
)
from app.models.user import User, UserProfile, UserPreference, UserRoleEnum, RefreshToken, UserSession
from app.models.gamification import UserGamification
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, RefreshTokenRequest, TokenResponse, UserShortResponse


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: UserRegisterRequest) -> User:
        # Check if email exists
        existing_user = await db.execute(select(User).where(User.email == data.email.lower()))
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        # Validate role
        try:
            role_enum = UserRoleEnum(data.role.upper())
        except ValueError:
            role_enum = UserRoleEnum.STUDENT

        hashed_pw = get_password_hash(data.password)
        new_user = User(
            email=data.email.lower(),
            hashed_password=hashed_pw,
            full_name=data.full_name,
            role=role_enum,
            is_active=True,
            is_verified=False
        )
        db.add(new_user)
        await db.flush()

        # Initialize profile, preference, and gamification records
        profile = UserProfile(user_id=new_user.id)
        preference = UserPreference(user_id=new_user.id)
        gamification = UserGamification(user_id=new_user.id)

        db.add_all([profile, preference, gamification])
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def login(
        db: AsyncSession,
        data: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == data.email.lower(), User.is_deleted == False))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support."
            )

        # Generate tokens
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": role_str}
        )
        raw_refresh_token = generate_secure_token(64)
        hashed_refresh = hash_token(raw_refresh_token)

        # Store refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh = RefreshToken(
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=expires_at
        )
        db.add(db_refresh)

        # Store session
        db_session = UserSession(
            user_id=user.id,
            session_token=hash_token(access_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        db.add(db_session)
        await db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserShortResponse.model_validate(user)
        )

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
        hashed_input = hash_token(refresh_token_str)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hashed_input,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Fetch user
        user_result = await db.execute(select(User).where(User.id == token_record.user_id, User.is_deleted == False))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Rotate refresh token: revoke current, issue new
        token_record.is_revoked = True

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": role_str}
        )
        new_raw_refresh = generate_secure_token(64)
        new_hashed_refresh = hash_token(new_raw_refresh)

        new_token_record = RefreshToken(
            user_id=user.id,
            token_hash=new_hashed_refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(new_token_record)
        await db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserShortResponse.model_validate(user)
        )

    @staticmethod
    async def logout(db: AsyncSession, user: User, token_str: str) -> bool:
        try:
            payload = decode_access_token(token_str)
            jti = payload.get("jti")
            if jti:
                await revoke_token_jti(jti)
        except Exception:
            pass

        # Mark active refresh tokens as revoked
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
        )
        await db.commit()
        return True

    @staticmethod
    async def logout_all(db: AsyncSession, user: User) -> bool:
        # Revoke all sessions and refresh tokens
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_revoked=True)
        )
        await db.commit()
        return True

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        user.hashed_password = get_password_hash(new_password)
        # Revoke all tokens to force re-login
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )
        await db.commit()
        return True

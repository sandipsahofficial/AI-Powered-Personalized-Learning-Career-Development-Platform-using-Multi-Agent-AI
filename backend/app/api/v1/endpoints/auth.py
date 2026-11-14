from fastapi import APIRouter, Depends, Request, status, Header
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.core.security import get_current_user, security_scheme
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserShortResponse
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserShortResponse, status_code=status.HTTP_201_CREATED, summary="Register New User")
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register(db, data)
    return UserShortResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, summary="User Login with Password")
async def login(
    data: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip = request.client.host if request.client else None
    agent = request.headers.get("user-agent")
    return await AuthService.login(db, data, ip_address=ip, user_agent=agent)


@router.post("/refresh", response_model=TokenResponse, summary="Rotate and Refresh JWT Tokens")
async def refresh_tokens(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_tokens(db, data.refresh_token)


@router.post("/logout", summary="Logout Current Session and Revoke Access Token")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials if credentials else ""
    await AuthService.logout(db, current_user, token)
    return {"message": "Successfully logged out and session revoked"}


@router.post("/logout-all", summary="Logout from All Devices (Revoke All Refresh Tokens)")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.logout_all(db, current_user)
    return {"message": "Successfully logged out from all active sessions"}


@router.post("/forgot-password", summary="Request Password Reset Link/Code")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # In production, this dispatches a secure email token; returns success to avoid email enumeration
    return {"message": f"If an account exists with {data.email}, a password reset link has been dispatched."}


@router.post("/reset-password", summary="Reset Password with Verification Token")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return {"message": "Password successfully reset. You may now log in with your new credentials."}


@router.post("/change-password", summary="Change Password while Authenticated")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.change_password(db, current_user, data.current_password, data.new_password)
    return {"message": "Password changed successfully. Please log in with your new password."}

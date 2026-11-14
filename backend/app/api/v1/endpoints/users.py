import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest, UserSessionResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=List[UserResponse], summary="List All Users (Admin Only)")
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_roles(["ORG_ADMIN", "SYS_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    users = await UserService.get_all_users(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User")
async def get_my_user(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse, summary="Update Current User Details")
async def update_my_user(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.email is not None:
        current_user.email = data.email.lower()
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/me/sessions", response_model=List[UserSessionResponse], summary="List Active Sessions for Current User")
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sessions = await UserService.get_sessions(db, current_user.id)
    return [UserSessionResponse.model_validate(s) for s in sessions]


@router.delete("/me/sessions/{session_id}", summary="Revoke a Specific Active Session")
async def revoke_my_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await UserService.revoke_session(db, current_user.id, session_id)
    return {"message": "Session revoked successfully"}

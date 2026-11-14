from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.profile import UserProfileResponse, UserProfileUpdateRequest
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, summary="Get Current User Profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await UserService.get_profile(db, current_user.id)
    return UserProfileResponse.model_validate(profile)


@router.put("/me", response_model=UserProfileResponse, summary="Replace Current User Profile")
@router.patch("/me", response_model=UserProfileResponse, summary="Update Current User Profile")
async def update_my_profile(
    data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await UserService.update_profile(db, current_user.id, data)
    return UserProfileResponse.model_validate(profile)

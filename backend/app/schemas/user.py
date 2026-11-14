import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    organization_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserSessionResponse(BaseModel):
    id: uuid.UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    is_revoked: bool

    model_config = {"from_attributes": True}

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: Optional[str] = Field(default=None, max_length=128)
    role: str = Field(default="STUDENT")
    terms_accepted: bool = Field(default=True)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if v is not None and "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: Optional[str] = Field(default=None, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if v is not None and "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UserShortResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserShortResponse

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

UserRole = Literal["admin", "sales_manager", "sales_executive"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "sales_executive"


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    """Fields a staff user is allowed to change on their own account."""

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirmation do not match.")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

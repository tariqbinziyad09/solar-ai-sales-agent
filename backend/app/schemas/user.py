"""
Staff User Schemas
==================

Schemas used by Admin for internal CRM staff management.

Customers are NOT stored here as CRM users.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

StaffRole = Literal[
    "admin",
    "sales_manager",
    "sales_executive",
]


class StaffUserCreate(BaseModel):
    """Create a new internal CRM staff account."""

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    role: StaffRole


class StaffUserResponse(BaseModel):
    """Safe staff response. Password hash is never returned."""

    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffStatusUpdate(BaseModel):
    """Activate or deactivate a staff account."""

    is_active: bool

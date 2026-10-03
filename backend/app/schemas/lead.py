from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class LeadBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=7, max_length=30)
    email: EmailStr | None = None
    city: str | None = Field(default=None, max_length=100)
    monthly_bill: float | None = Field(default=None, ge=0)
    interested_system: str | None = Field(default=None, max_length=50)
    budget: float | None = Field(default=None, ge=0)


class LeadCreate(LeadBase):
    source: str = Field(default="website", max_length=50)


class LeadResponse(LeadBase):
    id: int
    status: str
    source: str
    created_at: datetime

    # Qualification data is returned to the CRM frontend.
    qualification_score: int | None = None
    qualification_level: str | None = None

    # Read-only through the generic lead API.
    # Assignment changes must use the dedicated /assign endpoint.
    assigned_to_user_id: int | None = None

    # Follow-up information remains visible to authorized CRM staff.
    next_follow_up_at: datetime | None = None
    follow_up_note: str | None = None
    follow_up_completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LeadUpdate(BaseModel):
    """
    Fields that may be changed through PATCH /api/leads/{lead_id}.

    IMPORTANT:
    assigned_to_user_id is intentionally NOT included here.
    Lead assignment/reassignment must go through the dedicated
    RBAC-protected /api/leads/{lead_id}/assign endpoint.
    """

    status: LeadStatus | None = None
    next_follow_up_at: datetime | None = None
    follow_up_note: str | None = Field(default=None, max_length=500)
    follow_up_completed_at: datetime | None = None

"""
CRM Sales Intelligence Schemas
==============================

Response models used by the CRM Sales Intelligence API.

The purpose of these schemas is to combine useful lead,
qualification, solar requirement, and AI chat session
information into one structured API response.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeadChatSessionSummary(BaseModel):
    """
    Summary of an AI chat session associated with a lead.
    """

    model_config = ConfigDict(from_attributes=True)

    session_id: int = Field(gt=0)

    budget: float | None = None
    required_kw: float | None = None
    system_type: str | None = None
    needs_backup: bool | None = None

    created_at: datetime


class LeadSalesIntelligenceResponse(BaseModel):
    """
    Complete sales intelligence information for one CRM lead.
    """

    # --------------------------------------------------
    # CUSTOMER / LEAD INFORMATION
    # --------------------------------------------------
    lead_id: int = Field(gt=0)

    name: str
    phone: str
    email: str | None = None
    city: str | None = None

    # --------------------------------------------------
    # SALES INFORMATION
    # --------------------------------------------------
    status: str
    source: str

    qualification_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    qualification_level: str | None = None

    # --------------------------------------------------
    # SOLAR REQUIREMENTS
    # --------------------------------------------------
    budget: float | None = None
    interested_system: str | None = None
    monthly_bill: float | None = None

    # --------------------------------------------------
    # AI CONVERSATION INFORMATION
    # --------------------------------------------------
    chat_sessions: list[LeadChatSessionSummary] = Field(
        default_factory=list,
    )

    created_at: datetime
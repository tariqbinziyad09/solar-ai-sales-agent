"""
Proposal Schemas
================

Pydantic schemas used by the Proposal / Quotation Engine.

These schemas control:
- Proposal creation requests
- Proposal item responses
- Complete proposal responses
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    """
    Valid proposal lifecycle states.
    """

    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ProposalCreate(BaseModel):
    """
    Data required to generate a proposal.

    Pricing and proposal items are NOT accepted directly
    from the client. The backend will calculate them from
    the verified solar package.
    """

    lead_id: int = Field(gt=0)
    package_id: int = Field(gt=0)

    discount: float = Field(
        default=0,
        ge=0,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class ProposalItemResponse(BaseModel):
    """
    One product snapshot inside a proposal.
    """

    id: int
    product_id: int
    product_name: str

    quantity: int
    unit_price: float
    line_total: float

class ProposalStatusUpdate(BaseModel):
    """
    Request schema for changing proposal status.
    """

    status: ProposalStatus
class ProposalResponse(BaseModel):
    """
    Complete proposal returned by the API.
    """

    id: int

    proposal_number: str

    lead_id: int
    package_id: int

    status: ProposalStatus

    subtotal: float
    discount: float
    total_price: float

    notes: str | None = None

    items: list[ProposalItemResponse] = Field(
        default_factory=list,
    )

    created_at: datetime
    updated_at: datetime

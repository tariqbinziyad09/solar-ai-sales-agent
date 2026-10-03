"""
CRM Dashboard Schemas
=====================

Response models used by the CRM dashboard.

The dashboard combines lead qualification, sales pipeline,
proposal and revenue statistics.
"""

from pydantic import BaseModel, Field


class CRMDashboardSummary(BaseModel):
    """Summary statistics for the Solar AI Sales CRM dashboard."""

    total_leads: int = Field(ge=0)

    # Qualification statistics
    hot_leads: int = Field(ge=0)
    warm_leads: int = Field(ge=0)
    cold_leads: int = Field(ge=0)

    # Sales pipeline statistics
    new_leads: int = Field(ge=0)
    contacted_leads: int = Field(ge=0)
    qualified_leads: int = Field(ge=0)
    proposal_leads: int = Field(ge=0)
    won_leads: int = Field(ge=0)
    lost_leads: int = Field(ge=0)

    # Proposal / revenue analytics
    total_proposals: int = Field(ge=0)
    draft_proposals: int = Field(ge=0)
    sent_proposals: int = Field(ge=0)
    accepted_proposals: int = Field(ge=0)
    rejected_proposals: int = Field(ge=0)

    total_proposal_value: float = Field(ge=0)
    accepted_sales_value: float = Field(ge=0)

    # Percentage of leads that reached WON.
    conversion_rate: float = Field(ge=0, le=100)

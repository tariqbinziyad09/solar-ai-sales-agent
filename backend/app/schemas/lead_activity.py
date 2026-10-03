from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadActivityResponse(BaseModel):
    """
    One CRM timeline activity for a lead.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int

    activity_type: str
    description: str

    old_value: str | None = None
    new_value: str | None = None

    created_at: datetime

"""Pydantic schemas for CRM lead notes."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class LeadNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=5000)

class LeadNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    author_user_id: int
    author_name: str
    content: str
    created_at: datetime

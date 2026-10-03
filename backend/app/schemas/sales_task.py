"""Pydantic schemas for CRM sales tasks."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TaskPriority = Literal["low", "medium", "high"]
TaskStatus = Literal["pending", "completed"]


class SalesTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = "medium"
    due_at: datetime | None = None


class SalesTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_at: datetime | None = None


class SalesTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    title: str
    description: str | None
    priority: str
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

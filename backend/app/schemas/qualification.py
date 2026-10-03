"""
Lead Qualification Schemas
==========================

Defines the structured result produced by the
lead qualification engine.
"""

from enum import Enum

from pydantic import BaseModel, Field


class QualificationLevel(str, Enum):
    """Allowed lead qualification levels."""

    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class LeadQualificationResult(BaseModel):
    score: int = Field(
        ge=0,
        le=100,
    )

    level: QualificationLevel

    reasons: list[str] = Field(
        default_factory=list,
    )

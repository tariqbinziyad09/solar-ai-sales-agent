"""
Recommendation Schemas
======================

Defines customer requirements used by the
solar package recommendation engine.
"""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """
    Structured customer requirements.

    Later, the AI layer will automatically extract
    these values from a natural-language conversation.
    """

    # Customer's maximum available budget.
    budget: float | None = Field(
        default=None,
        gt=0,
    )

    # Desired system size.
    # Example: 5kW, 10kW, 15kW
    required_kw: float | None = Field(
        default=None,
        gt=0,
    )

    # hybrid / on-grid / off-grid
    system_type: str | None = Field(
        default=None,
        max_length=50,
    )

    # Customer may explicitly request backup.
    needs_backup: bool | None = None


class RecommendedPackage(BaseModel):
    """
    One ranked solar package recommendation.
    """

    package_id: int
    name: str
    system_size_kw: float
    system_type: str
    package_price: float
    match_score: float

    # Human-readable explanation of the recommendation.
    reasons: list[str]


class RecommendationResponse(BaseModel):
    """
    Complete recommendation engine response.
    """

    total_matches: int
    recommendations: list[RecommendedPackage]

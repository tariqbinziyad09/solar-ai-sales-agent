"""
Solar Recommendation API
========================

Receives structured customer requirements
and returns matching packages from SQL Server.
"""

from typing import Annotated

from app.database.database import get_db
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation_service import recommend_packages
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"],
)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
def get_recommendations(
    requirements: RecommendationRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Recommend solar packages based on customer requirements.

    Flow:
        Customer Requirements
                ↓
        RecommendationRequest
                ↓
        Recommendation Engine
                ↓
           SQL Server
                ↓
        Matching Packages
    """

    try:
        recommendations = recommend_packages(
            db=db,
            requirements=requirements,
        )

        return {
            "total_matches": len(recommendations),
            "recommendations": [
                {
                    "reasons": result["reasons"],
                    "package_id": result["package"].id,
                    "name": result["package"].name,
                    "system_size_kw": result["package"].system_size_kw,
                    "system_type": result["package"].system_type,
                    "package_price": result["package"].package_price,
                    "match_score": result["match_score"],
                }
                for result in recommendations
            ],
        }

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate recommendations.",
        ) from error

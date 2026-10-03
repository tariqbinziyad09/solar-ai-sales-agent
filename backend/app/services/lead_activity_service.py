"""
Lead Activity Service
=====================

Handles creation and retrieval of CRM timeline activities.

Examples:
- Lead created
- Status changed
- Qualification updated
"""

from app.models.lead_activity import LeadActivity
from sqlalchemy.orm import Session


def create_lead_activity(
    db: Session,
    lead_id: int,
    activity_type: str,
    description: str,
    old_value: str | None = None,
    new_value: str | None = None,
) -> LeadActivity:
    """
    Create a new activity/timeline entry for a lead.
    """

    activity = LeadActivity(
        lead_id=lead_id,
        activity_type=activity_type,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


def get_lead_activities(
    db: Session,
    lead_id: int,
) -> list[LeadActivity]:
    """
    Return all activities for a lead.

    Newest activities are returned first.
    """

    return (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
        .all()
    )

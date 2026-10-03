"""
Lead Activity Model
===================

Stores the history/timeline of important CRM events for a lead.

Examples:
- Lead created
- Qualification updated
- Status changed
- Proposal generated
- Lead won/lost
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    # Unique activity record ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Lead this activity belongs to
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Type of activity
    # Examples:
    # lead_created, status_changed, qualification_updated
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Short human-readable description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Optional previous/new values.
    # Useful for events like:
    # contacted -> qualified
    old_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    new_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ORM relationship
    lead = relationship(
        "Lead",
        back_populates="activities",
    )

"""
Proposal Model
==============

Stores a sales quotation/proposal generated for a CRM lead.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )

    package_id: Mapped[int] = mapped_column(
        ForeignKey("solar_packages.id"),
        nullable=False,
        index=True,
    )

    proposal_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
    )

    subtotal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    discount: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    total_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # --------------------------------------------------
    # PROPOSAL ITEMS RELATIONSHIP
    # --------------------------------------------------
    lead = relationship(
    "Lead",
    back_populates="proposals",
)
    items = relationship(
        "ProposalItem",
        back_populates="proposal",
        cascade="all, delete-orphan",
    )
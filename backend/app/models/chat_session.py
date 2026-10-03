"""
Chat Session Model
==================

Stores solar requirements, appliance/energy usage,
conversation language, CRM information, sales intent
and quotation intent collected during a customer's
conversation with the AI Sales Agent.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.database import Base


class ChatSession(Base):
    """Persistent conversation memory for the AI Solar Sales Agent."""

    __tablename__ = "chat_sessions"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ========================================================
    # SOLAR REQUIREMENTS
    # ========================================================

    budget: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    required_kw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    system_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    needs_backup: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # ========================================================
    # ENERGY / APPLIANCE USAGE
    # ========================================================

    # Monthly electricity consumption in kWh/units.
    monthly_units: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # JSON-serialized list of appliance usage dictionaries.
    # Text keeps the structure flexible for different customer
    # loads without adding one database column per appliance.
    appliance_usage_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # CONVERSATION LANGUAGE
    # ========================================================

    # Supported values:
    #     "roman_urdu"
    #     "english"
    #
    # This preserves language across short replies such as:
    # "yes", "han", "5kw", "800000", and phone numbers.
    preferred_language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # ========================================================
    # CRM / CUSTOMER INFORMATION
    # ========================================================

    customer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    customer_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    customer_email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    customer_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # SALES INTENT
    # ========================================================

    wants_sales_contact: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # ========================================================
    # QUOTATION INTENT
    # ========================================================

    wants_quotation: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # ========================================================
    # CRM LEAD LINK
    # ========================================================

    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id"),
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

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

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    lead = relationship(
        "Lead",
        back_populates="chat_sessions",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )

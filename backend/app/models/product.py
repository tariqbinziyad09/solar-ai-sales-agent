"""
Base Product Model
==================

Stores information common to every product sold
by the solar company.

Specific technical specifications are stored
in specialized tables such as:

- SolarPanel
- Inverter
- Battery
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Product(Base):
    """
    Base catalog entry for every solar product.

    Examples:
        Longi Hi-MO Solar Panel
        Knox 10kW Hybrid Inverter
        Lithium Battery
    """

    __tablename__ = "products"

    # Unique product ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Product display name
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Manufacturer / brand
    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # panel / inverter / battery
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Optional SKU used by the company
    sku: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    # Human-readable product information
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Current selling price
    price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Whether this product can currently be sold
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

"""
Solar Package Model
===================

Represents a complete solar system offered to customers.

A package can contain multiple products through
the PackageItem table.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class SolarPackage(Base):
    """Represents a complete solar sales package."""

    __tablename__ = "solar_packages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Nominal system size.
    # Example: 5kW, 10kW, 15kW
    system_size_kw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    # on-grid / hybrid / off-grid
    system_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Final selling price of complete package.
    package_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # One package can contain many package items.
    items = relationship(
        "PackageItem",
        back_populates="package",
        cascade="all, delete-orphan",
    )

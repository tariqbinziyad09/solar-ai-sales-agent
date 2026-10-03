"""
Solar Battery Model
===================

Stores specifications for batteries used
with solar energy systems.
"""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Battery(Base):
    """Technical specifications for a solar battery."""

    __tablename__ = "batteries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Example:
    # Lithium-ion / LiFePO4 / Lead Acid
    chemistry: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Energy storage capacity
    # Example: 5.12 kWh
    capacity_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Example: 48V / 51.2V
    voltage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Expected charge/discharge cycles
    cycle_life: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    warranty_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    product = relationship("Product")

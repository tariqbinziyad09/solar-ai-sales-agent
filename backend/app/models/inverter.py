"""
Solar Inverter Model
====================

Stores technical specifications specific
to solar inverters.
"""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Inverter(Base):
    """Technical specifications for an inverter."""

    __tablename__ = "inverters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Example: 10 kW
    power_kw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # on-grid / hybrid / off-grid
    inverter_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # single-phase / three-phase
    phase: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Number of MPPT trackers
    mppt_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    efficiency: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    warranty_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    product = relationship("Product")

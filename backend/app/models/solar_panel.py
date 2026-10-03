"""
Solar Panel Model
=================

Stores technical specifications that apply
specifically to photovoltaic solar panels.
"""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class SolarPanel(Base):
    """Technical specifications for a solar panel."""

    __tablename__ = "solar_panels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Connect this specification to the base Product.
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Example: 585 watts
    wattage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Example: Monocrystalline / N-Type / TOPCon
    technology: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Example: 22.6 (%)
    efficiency: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    warranty_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationship back to the common product record.
    product = relationship("Product")

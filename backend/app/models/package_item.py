"""
Package Item Model
==================

Connects solar packages with products.

Example:
10kW Package
    → Product #1 × 18
    → Product #5 × 1
    → Product #8 × 2
"""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class PackageItem(Base):
    """A product and its quantity inside a solar package."""

    __tablename__ = "package_items"

    # Prevent the same product from being added twice
    # to the same package.
    __table_args__ = (
        UniqueConstraint(
            "package_id",
            "product_id",
            name="uq_package_product",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    package_id: Mapped[int] = mapped_column(
        ForeignKey(
            "solar_packages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    package = relationship(
        "SolarPackage",
        back_populates="items",
    )

    product = relationship("Product")

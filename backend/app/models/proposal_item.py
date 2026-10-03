"""
Proposal Item Model
===================

Stores individual products included in a sales proposal.

Each item keeps a price snapshot so an old quotation
does not change when the product catalog price changes.
"""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ProposalItem(Base):
    __tablename__ = "proposal_items"

    # --------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # --------------------------------------------------
    # PARENT PROPOSAL
    # --------------------------------------------------
    proposal_id: Mapped[int] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Original catalog product.
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------
    # PRODUCT SNAPSHOT
    # --------------------------------------------------
    # Store the name in the quotation itself so historical
    # proposals remain understandable if catalog data changes.
    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Price of ONE unit when proposal was generated.
    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # quantity × unit_price
    line_total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # --------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------
    proposal = relationship(
        "Proposal",
        back_populates="items",
    )
items = relationship(
    "ProposalItem",
    back_populates="proposal",
    cascade="all, delete-orphan",
)
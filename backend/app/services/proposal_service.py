"""
Proposal Service
================

Creates professional sales proposals from verified CRM leads
and solar packages.

Important:
- Lead must exist.
- Package must exist and be active.
- Proposal pricing comes from the package price.
- Product information and unit prices are frozen as snapshots.
- Client cannot directly control subtotal or total price.
"""

from uuid import uuid4

from app.models.lead import Lead
from app.models.proposal import Proposal
from app.models.proposal_item import ProposalItem
from app.models.solar_package import SolarPackage
from app.schemas.proposal import ProposalCreate, ProposalStatus
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def generate_proposal_number(proposal_id: int) -> str:
    """Generate a human-readable proposal number."""
    return f"PROP-{proposal_id:06d}"


def get_existing_proposal_for_lead_package(
    db: Session,
    lead_id: int,
    package_id: int,
) -> Proposal | None:
    """
    Return the newest existing proposal for the same lead + package.

    This prevents the AI Sales Agent from creating a duplicate quotation
    when the customer asks for the same quotation again.

    A different recommended package is allowed to create a new proposal,
    because that represents a materially different quotation.
    """
    return (
        db.query(Proposal)
        .filter(
            Proposal.lead_id == lead_id,
            Proposal.package_id == package_id,
        )
        .order_by(Proposal.created_at.desc(), Proposal.id.desc())
        .first()
    )


def create_proposal(
    db: Session,
    proposal_data: ProposalCreate,
) -> Proposal:
    """Create a proposal from an existing lead and solar package."""

    lead = db.get(Lead, proposal_data.lead_id)
    if lead is None:
        raise ValueError("Lead not found.")

    solar_package = db.get(SolarPackage, proposal_data.package_id)
    if solar_package is None:
        raise ValueError("Solar package not found.")
    if not solar_package.is_active:
        raise ValueError("Solar package is not active.")
    if not solar_package.items:
        raise ValueError("Solar package does not contain any products.")

    subtotal = float(solar_package.package_price)
    discount = float(proposal_data.discount)

    if discount > subtotal:
        raise ValueError("Discount cannot be greater than proposal subtotal.")

    total_price = subtotal - discount

    try:
        temporary_number = f"TEMP-{uuid4().hex}"

        proposal = Proposal(
            lead_id=lead.id,
            package_id=solar_package.id,
            proposal_number=temporary_number,
            status="draft",
            subtotal=subtotal,
            discount=discount,
            total_price=total_price,
            notes=proposal_data.notes,
        )

        db.add(proposal)
        db.flush()

        proposal.proposal_number = generate_proposal_number(proposal.id)

        for package_item in solar_package.items:
            product = package_item.product

            if product is None:
                raise ValueError("A package item references an invalid product.")

            if product.price is None:
                raise ValueError(
                    f"Product '{product.name}' does not have a price."
                )

            unit_price = float(product.price)
            quantity = package_item.quantity

            proposal_item = ProposalItem(
                proposal_id=proposal.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                line_total=unit_price * quantity,
            )

            db.add(proposal_item)

        db.commit()
        db.refresh(proposal)
        return proposal

    except (SQLAlchemyError, ValueError):
        db.rollback()
        raise


def get_proposal_by_id(
    db: Session,
    proposal_id: int,
) -> Proposal | None:
    """Return a proposal by its database ID."""
    return db.get(Proposal, proposal_id)


def validate_proposal_status_transition(
    current_status: str,
    new_status: ProposalStatus,
) -> bool:
    """Validate allowed proposal lifecycle transitions."""
    allowed_transitions: dict[str, set[str]] = {
        "draft": {"sent"},
        "sent": {"accepted", "rejected"},
        "accepted": set(),
        "rejected": set(),
    }

    allowed_next_statuses = allowed_transitions.get(current_status, set())
    return new_status.value in allowed_next_statuses


def update_proposal_status(
    db: Session,
    proposal: Proposal,
    new_status: ProposalStatus,
) -> Proposal:
    """Update proposal status after transition validation."""
    proposal.status = new_status.value

    try:
        db.commit()
        db.refresh(proposal)
        return proposal
    except SQLAlchemyError:
        db.rollback()
        raise


def get_all_proposals(db: Session) -> list[Proposal]:
    """Return all proposals, newest first."""
    return db.query(Proposal).order_by(Proposal.created_at.desc()).all()

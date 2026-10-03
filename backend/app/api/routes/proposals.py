"""
Proposal API Routes
===================
API endpoints for creating and managing
customer sales proposals / quotations.
"""

from typing import Annotated

from app.database.database import get_db
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadStatus, LeadUpdate
from app.schemas.proposal import (
    ProposalCreate,
    ProposalResponse,
    ProposalStatusUpdate,
)
from app.services.lead_activity_service import create_lead_activity
from app.services.lead_service import (
    update_lead,
    validate_status_transition,
)
from app.services.proposal_pdf_service import generate_proposal_pdf
from app.services.proposal_service import (
    create_proposal,
    get_all_proposals,
    get_proposal_by_id,
    update_proposal_status,
    validate_proposal_status_transition,
)
from app.services.rbac_service import ROLE_SALES_EXECUTIVE, require_staff
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/proposals",
    tags=["Proposals"],
)


def ensure_proposal_access(
    db: Session,
    proposal,
    current_user: User,
):
    """Allow executives to access proposals only for assigned leads."""
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found.",
        )

    if current_user.role == ROLE_SALES_EXECUTIVE:
        lead = db.get(Lead, proposal.lead_id)
        if lead is None or lead.assigned_to_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found.",
            )

    return proposal


def ensure_proposal_lead_access(
    db: Session,
    lead_id: int,
    current_user: User,
) -> Lead:
    """Allow executives to create proposals only for assigned leads."""
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )

    if (
        current_user.role == ROLE_SALES_EXECUTIVE
        and lead.assigned_to_user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )

    return lead


# ============================================================
# CREATE PROPOSAL
# POST /api/proposals
# ============================================================
@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_proposal(
    proposal_data: ProposalCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Create a new sales proposal for a CRM lead.
    The backend:
    - verifies the lead
    - verifies the solar package
    - calculates pricing
    - creates product snapshots
    - generates the proposal number
    - records proposal creation in CRM timeline
    """
    try:
        ensure_proposal_lead_access(
            db=db,
            lead_id=proposal_data.lead_id,
            current_user=current_user,
        )

        proposal = create_proposal(
            db=db,
            proposal_data=proposal_data,
        )
        create_lead_activity(
            db=db,
            lead_id=proposal.lead_id,
            activity_type="proposal_created",
            description=(
                f"Proposal {proposal.proposal_number} created "
                f"with final quotation PKR "
                f"{proposal.total_price:,.0f}."
            ),
            old_value=None,
            new_value=proposal.proposal_number,
        )
        return proposal
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create proposal.",
        ) from error


# ============================================================
# GET ALL PROPOSALS
# GET /api/proposals
# ============================================================
@router.get(
    "",
    response_model=list[ProposalResponse],
    status_code=status.HTTP_200_OK,
)
def get_proposals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """Return proposals visible to the logged-in CRM staff member."""
    try:
        proposals = get_all_proposals(db=db)

        if current_user.role != ROLE_SALES_EXECUTIVE:
            return proposals

        visible_proposals = []
        for proposal in proposals:
            lead = db.get(Lead, proposal.lead_id)
            if lead is not None and lead.assigned_to_user_id == current_user.id:
                visible_proposals.append(proposal)

        return visible_proposals
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load proposals.",
        ) from error


# ============================================================
# DOWNLOAD PROPOSAL PDF
# GET /api/proposals/{proposal_id}/pdf
# ============================================================
@router.get(
    "/{proposal_id}/pdf",
    response_class=StreamingResponse,
)
def download_proposal_pdf(
    proposal_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """Generate and download a PDF quotation."""
    proposal = get_proposal_by_id(
        db=db,
        proposal_id=proposal_id,
    )
    proposal = ensure_proposal_access(
        db=db,
        proposal=proposal,
        current_user=current_user,
    )
    pdf_buffer = generate_proposal_pdf(proposal)
    filename = f"{proposal.proposal_number}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================
# GET SINGLE PROPOSAL
# GET /api/proposals/{proposal_id}
# ============================================================
@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse,
    status_code=status.HTTP_200_OK,
)
def get_proposal(
    proposal_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """Get one proposal by its ID."""
    proposal = get_proposal_by_id(
        db=db,
        proposal_id=proposal_id,
    )
    proposal = ensure_proposal_access(
        db=db,
        proposal=proposal,
        current_user=current_user,
    )
    return proposal


# ============================================================
# CRM SYNC
# ============================================================
def sync_accepted_proposal_with_crm(
    db: Session,
    proposal,
) -> None:
    """
    Synchronize an accepted proposal with its CRM lead.
    AI-created leads can still be in the "new" stage when their
    quotation is accepted. Instead of bypassing the CRM pipeline,
    this function advances the lead through every valid stage:
        new -> contacted -> qualified -> proposal -> won
    If the lead is already part-way through the pipeline, only the
    remaining transitions are applied.
    Won/lost leads are left unchanged.
    """
    lead = db.get(Lead, proposal.lead_id)
    if lead is None:
        return
    # Terminal states must never be overwritten automatically.
    if lead.status in {"won", "lost"}:
        return
    pipeline = [
        LeadStatus.NEW,
        LeadStatus.CONTACTED,
        LeadStatus.QUALIFIED,
        LeadStatus.PROPOSAL,
        LeadStatus.WON,
    ]
    current_status = LeadStatus(lead.status)
    try:
        current_index = pipeline.index(current_status)
    except ValueError:
        return
    # Move through the normal CRM pipeline one valid step at a time.
    for next_status in pipeline[current_index + 1 :]:
        if not validate_status_transition(
            current_status=lead.status,
            new_status=next_status,
        ):
            return
        old_status = lead.status
        update_lead(
            db=db,
            lead=lead,
            lead_data=LeadUpdate(status=next_status),
        )
        activity_type = (
            "sale_won" if next_status == LeadStatus.WON else "status_changed"
        )
        if next_status == LeadStatus.WON:
            description = (
                f"Lead marked as won after accepting proposal "
                f"{proposal.proposal_number}."
            )
        else:
            description = (
                f"Lead status automatically advanced from "
                f"{old_status} to {next_status.value} after "
                f"proposal {proposal.proposal_number} was accepted."
            )
        create_lead_activity(
            db=db,
            lead_id=lead.id,
            activity_type=activity_type,
            description=description,
            old_value=old_status,
            new_value=next_status.value,
        )
        # Refresh so the next transition validates against current DB state.
        db.refresh(lead)


# ============================================================
# CHANGE PROPOSAL STATUS
# PATCH /api/proposals/{proposal_id}/status
# ============================================================
@router.patch(
    "/{proposal_id}/status",
    response_model=ProposalResponse,
    status_code=status.HTTP_200_OK,
)
def change_proposal_status(
    proposal_id: int,
    status_data: ProposalStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Change proposal status using the controlled lifecycle:
        draft -> sent -> accepted/rejected
    When a proposal becomes accepted, its related CRM lead is
    advanced through the valid lead pipeline until it reaches WON.
    """
    try:
        # 1. Find proposal.
        proposal = get_proposal_by_id(
            db=db,
            proposal_id=proposal_id,
        )
        proposal = ensure_proposal_access(
            db=db,
            proposal=proposal,
            current_user=current_user,
        )
        old_status = proposal.status
        # 2. Validate proposal transition.
        is_valid = validate_proposal_status_transition(
            current_status=old_status,
            new_status=status_data.status,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Proposal cannot move from "
                    f"'{old_status}' to "
                    f"'{status_data.status.value}'."
                ),
            )
        # 3. Update proposal.
        updated_proposal = update_proposal_status(
            db=db,
            proposal=proposal,
            new_status=status_data.status,
        )
        # 4. Record proposal status event.
        create_lead_activity(
            db=db,
            lead_id=updated_proposal.lead_id,
            activity_type="proposal_status_changed",
            description=(
                f"Proposal {updated_proposal.proposal_number} "
                f"status changed from {old_status} to "
                f"{updated_proposal.status}."
            ),
            old_value=old_status,
            new_value=updated_proposal.status,
        )
        # 5. Accepted quotation = won sale.
        if updated_proposal.status == "accepted":
            sync_accepted_proposal_with_crm(
                db=db,
                proposal=updated_proposal,
            )
        # Refresh proposal after CRM synchronization.
        db.refresh(updated_proposal)
        return updated_proposal
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update proposal status.",
        ) from error

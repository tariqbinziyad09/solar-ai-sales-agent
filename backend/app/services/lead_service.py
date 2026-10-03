r"""

Lead Service

\\============

This module contains the business logic for lead management.

Why use a service layer?

\\------------------------

API routes should mainly handle HTTP requests and responses.

Database/business operations are kept here so the code remains

organized, reusable, and easier to test.

Create Lead Flow

\\----------------

Validated LeadCreate

        ↓

Lead Service

        ↓

Create SQLAlchemy Lead object

        ↓

Add to database session

        ↓

Commit transaction

        ↓

Refresh object

        ↓

Return saved Lead

"""

from app.models.lead import Lead
from app.models.proposal import Proposal
from app.schemas.crm import CRMDashboardSummary
from app.schemas.lead import LeadCreate, LeadStatus, LeadUpdate
from app.schemas.sales_intelligence import (
    LeadChatSessionSummary,
    LeadSalesIntelligenceResponse,
)
from app.services.lead_activity_service import create_lead_activity
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def validate_status_transition(
    current_status: str,
    new_status: LeadStatus,
) -> bool:
    """

    Validate whether a lead can move from its current

    CRM pipeline stage to the requested new stage.

    Allowed pipeline:

        new -> contacted -> qualified -> proposal -> won

         |         |            |           |

         └-> lost  └-> lost     └-> lost    └-> lost

    Won and lost are terminal states.

    """

    allowed_transitions: dict[str, set[str]] = {
        "new": {
            "contacted",
            "lost",
        },
        "contacted": {
            "qualified",
            "lost",
        },
        "qualified": {
            "proposal",
            "lost",
        },
        "proposal": {
            "won",
            "lost",
        },
        "won": set(),
        "lost": set(),
    }

    allowed_next_statuses = allowed_transitions.get(
        current_status,
        set(),
    )

    return new_status.value in allowed_next_statuses


def get_all_leads(db: Session) -> list[Lead]:
    """

    Retrieve all sales leads from the database.

    Args:

        db:

            Active SQLAlchemy database session.

    Returns:

        list[Lead]:

            List of all leads stored in SQL Server.

    Flow:

        Service receives DB session

                ↓

        Query Lead table

                ↓

        Order by newest lead first

                ↓

        SQL Server executes query

                ↓

        Return Lead objects

    """

    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()

    return leads


def get_filtered_leads(
    db: Session,
    status: str | None = None,
    qualification_level: str | None = None,
    city: str | None = None,
    search: str | None = None,
) -> list[Lead]:
    """

    Return CRM leads using optional server-side filters.

    Search currently checks:

    - customer name

    - phone number

    - email

    """

    query = db.query(Lead)

    if status is not None:
        query = query.filter(Lead.status == status)

    if qualification_level is not None:
        query = query.filter(Lead.qualification_level == qualification_level)

    if city is not None:
        query = query.filter(Lead.city.ilike(city))

    if search is not None and search.strip():
        search_value = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Lead.name.ilike(search_value),
                Lead.phone.ilike(search_value),
                Lead.email.ilike(search_value),
            )
        )

    return query.order_by(Lead.created_at.desc()).all()


def get_lead_by_id(db: Session, lead_id: int) -> Lead | None:
    """

    Retrieve a single lead by its unique ID.

    Returns:

        Lead | None:

            Lead if found, otherwise None.

    """

    return db.query(Lead).filter(Lead.id == lead_id).first()


def create_lead(db: Session, lead_data: LeadCreate) -> Lead:
    """

    Create and save a new sales lead.

    After the lead is successfully created, a CRM timeline

    activity is also recorded automatically.

    Args:

        db:

            Active SQLAlchemy database session.

        lead_data:

            Customer information already validated

            by the LeadCreate Pydantic schema.

    Returns:

        Lead:

            The newly created database record.

    Raises:

        SQLAlchemyError:

            If the database operation fails.

    """

    # --------------------------------------------------

    # 1. BUILD LEAD DATABASE OBJECT

    # --------------------------------------------------

    new_lead = Lead(
        name=lead_data.name,
        phone=lead_data.phone,
        email=lead_data.email,
        city=lead_data.city,
        monthly_bill=lead_data.monthly_bill,
        interested_system=lead_data.interested_system,
        budget=lead_data.budget,
        source=lead_data.source,
    )

    try:
        # --------------------------------------------------

        # 2. SAVE LEAD

        # --------------------------------------------------

        db.add(new_lead)

        # Commit first so SQL Server generates the lead ID.

        db.commit()

        # Reload generated values such as ID and created_at.

        db.refresh(new_lead)

        # --------------------------------------------------

        # 3. CREATE CRM TIMELINE ACTIVITY

        # --------------------------------------------------

        create_lead_activity(
            db=db,
            lead_id=new_lead.id,
            activity_type="lead_created",
            description=(f"Lead created from source '{new_lead.source}'."),
            old_value=None,
            new_value=new_lead.status,
        )

        # --------------------------------------------------

        # 4. RETURN CREATED LEAD

        # --------------------------------------------------

        return new_lead

    except SQLAlchemyError:
        # Roll back the current failed transaction.

        db.rollback()

        raise


def update_lead(
    db: Session,
    lead: Lead,
    lead_data: LeadUpdate,
) -> Lead:
    """

    Update an existing sales lead.

    Args:

        db:

            Active SQLAlchemy database session.

        lead:

            Existing Lead database object.

        lead_data:

            Validated fields that should be updated.

    Returns:

        Lead:

            Updated lead record.

    Flow:

        Existing Lead

             ↓

        LeadUpdate Schema

             ↓

        Extract changed fields

             ↓

        Update Lead object

             ↓

        Commit transaction

             ↓

        Refresh object

             ↓

        Return updated Lead

    """

    # exclude_unset=True means only fields actually supplied

    # by the client will be included in the update.

    update_data = lead_data.model_dump(exclude_unset=True)

    # Apply each supplied field to the SQLAlchemy object.

    for field, value in update_data.items():
        setattr(lead, field, value)

    try:
        db.commit()

        db.refresh(lead)

        return lead

    except SQLAlchemyError:
        # Undo the transaction if the update fails.

        db.rollback()

        raise


def delete_lead(db: Session, lead: Lead) -> None:
    """

    Delete an existing sales lead from the database.

    Args:

        db:

            Active SQLAlchemy database session.

        lead:

            Existing Lead object that should be deleted.

    Flow:

        Existing Lead

             ↓

        Mark for deletion

             ↓

        Commit transaction

             ↓

        Record removed from SQL Server

    Raises:

        SQLAlchemyError:

            If the database operation fails.

    """

    try:
        # Mark the lead for deletion.

        db.delete(lead)

        # Permanently apply the deletion in SQL Server.

        db.commit()

    except SQLAlchemyError:
        # Undo the transaction if deletion fails.

        db.rollback()

        raise


def get_crm_dashboard_summary(
    db: Session,
    assigned_to_user_id: int | None = None,
) -> CRMDashboardSummary:
    """
    Calculate CRM dashboard analytics.

    Admin / Sales Manager:
        assigned_to_user_id=None returns company-wide analytics.

    Sales Executive:
        assigned_to_user_id=<user id> returns analytics only for leads
        assigned to that executive. Proposal and sales-value analytics
        are scoped through the lead relationship as well.
    """

    lead_query = db.query(Lead)
    if assigned_to_user_id is not None:
        lead_query = lead_query.filter(Lead.assigned_to_user_id == assigned_to_user_id)
    total_leads = lead_query.count()

    def count_qualification(level: str) -> int:
        query = db.query(func.count(Lead.id)).filter(Lead.qualification_level == level)
        if assigned_to_user_id is not None:
            query = query.filter(Lead.assigned_to_user_id == assigned_to_user_id)
        return query.scalar() or 0

    def count_status(lead_status: str) -> int:
        query = db.query(func.count(Lead.id)).filter(Lead.status == lead_status)
        if assigned_to_user_id is not None:
            query = query.filter(Lead.assigned_to_user_id == assigned_to_user_id)
        return query.scalar() or 0

    hot_leads = count_qualification("hot")
    warm_leads = count_qualification("warm")
    cold_leads = count_qualification("cold")
    new_leads = count_status("new")
    contacted_leads = count_status("contacted")
    qualified_leads = count_status("qualified")
    proposal_leads = count_status("proposal")
    won_leads = count_status("won")
    lost_leads = count_status("lost")

    def proposal_query():
        query = db.query(Proposal)
        if assigned_to_user_id is not None:
            query = query.join(
                Lead,
                Proposal.lead_id == Lead.id,
            ).filter(Lead.assigned_to_user_id == assigned_to_user_id)
        return query

    total_proposals = proposal_query().count()

    def count_proposal_status(proposal_status: str) -> int:
        return proposal_query().filter(Proposal.status == proposal_status).count()

    draft_proposals = count_proposal_status("draft")
    sent_proposals = count_proposal_status("sent")
    accepted_proposals = count_proposal_status("accepted")
    rejected_proposals = count_proposal_status("rejected")

    total_value_query = db.query(func.sum(Proposal.total_price))
    if assigned_to_user_id is not None:
        total_value_query = total_value_query.join(
            Lead,
            Proposal.lead_id == Lead.id,
        ).filter(Lead.assigned_to_user_id == assigned_to_user_id)
    total_proposal_value = total_value_query.scalar() or 0

    accepted_value_query = db.query(func.sum(Proposal.total_price)).filter(
        Proposal.status == "accepted"
    )
    if assigned_to_user_id is not None:
        accepted_value_query = accepted_value_query.join(
            Lead,
            Proposal.lead_id == Lead.id,
        ).filter(Lead.assigned_to_user_id == assigned_to_user_id)
    accepted_sales_value = accepted_value_query.scalar() or 0

    conversion_rate = (won_leads / total_leads) * 100 if total_leads > 0 else 0

    return CRMDashboardSummary(
        total_leads=total_leads,
        hot_leads=hot_leads,
        warm_leads=warm_leads,
        cold_leads=cold_leads,
        new_leads=new_leads,
        contacted_leads=contacted_leads,
        qualified_leads=qualified_leads,
        proposal_leads=proposal_leads,
        won_leads=won_leads,
        lost_leads=lost_leads,
        total_proposals=total_proposals,
        draft_proposals=draft_proposals,
        sent_proposals=sent_proposals,
        accepted_proposals=accepted_proposals,
        rejected_proposals=rejected_proposals,
        total_proposal_value=float(total_proposal_value),
        accepted_sales_value=float(accepted_sales_value),
        conversion_rate=round(conversion_rate, 1),
    )


def get_lead_sales_intelligence(
    db: Session,
    lead_id: int,
) -> LeadSalesIntelligenceResponse | None:
    """

    Build complete CRM sales intelligence for one lead.

    Combines:

    - Customer information

    - CRM pipeline information

    - Qualification score

    - Solar requirements

    - Associated AI chat sessions

    Returns None if the lead does not exist.

    """

    # --------------------------------------------------

    # FIND LEAD

    # --------------------------------------------------

    lead = get_lead_by_id(
        db=db,
        lead_id=lead_id,
    )

    if lead is None:
        return None

    # --------------------------------------------------

    # BUILD CHAT SESSION SUMMARIES

    # --------------------------------------------------

    chat_sessions = [
        LeadChatSessionSummary(
            session_id=session.id,
            budget=session.budget,
            required_kw=session.required_kw,
            system_type=session.system_type,
            needs_backup=session.needs_backup,
            created_at=session.created_at,
        )
        for session in lead.chat_sessions
    ]

    # --------------------------------------------------

    # BUILD COMPLETE SALES INTELLIGENCE RESPONSE

    # --------------------------------------------------

    return LeadSalesIntelligenceResponse(
        lead_id=lead.id,
        name=lead.name,
        phone=lead.phone,
        email=lead.email,
        city=lead.city,
        status=lead.status,
        source=lead.source,
        qualification_score=lead.qualification_score,
        qualification_level=lead.qualification_level,
        budget=lead.budget,
        interested_system=lead.interested_system,
        monthly_bill=lead.monthly_bill,
        chat_sessions=chat_sessions,
        created_at=lead.created_at,
    )

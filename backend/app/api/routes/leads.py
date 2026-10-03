from typing import Annotated

from app.database.database import get_db
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.user import User
from app.schemas.crm import CRMDashboardSummary
from app.schemas.lead import (
    LeadCreate,
    LeadResponse,
    LeadStatus,
    LeadUpdate,
)
from app.schemas.lead_activity import LeadActivityResponse
from app.schemas.lead_note import LeadNoteCreate, LeadNoteResponse
from app.schemas.qualification import QualificationLevel
from app.schemas.sales_intelligence import LeadSalesIntelligenceResponse
from app.schemas.sales_task import SalesTaskCreate, SalesTaskResponse, SalesTaskUpdate
from app.services.lead_activity_service import (
    create_lead_activity,
    get_lead_activities,
)
from app.services.lead_note_service import (
    create_lead_note,
    delete_lead_note,
    get_lead_note,
    get_lead_notes,
    update_lead_note,
)
from app.services.lead_service import (
    create_lead,
    delete_lead,
    get_crm_dashboard_summary,
    get_filtered_leads,
    get_lead_by_id,
    get_lead_sales_intelligence,
    update_lead,
    validate_status_transition,
)
from app.services.rbac_service import (
    ROLE_ADMIN,
    ROLE_SALES_EXECUTIVE,
    ROLE_SALES_MANAGER,
    require_manager_or_admin,
    require_staff,
)
from app.services.sales_task_service import (
    create_task,
    delete_task,
    get_lead_tasks,
    get_open_tasks,
    get_task,
    update_task,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class LeadAssignmentRequest(BaseModel):
    """
    Staff member that should own the lead.
    Pass null to unassign the lead.
    """

    assigned_to_user_id: int | None = None


router = APIRouter(
    prefix="/api/leads",
    tags=["Leads"],
)


def ensure_lead_access(
    lead: Lead | None,
    current_user: User,
) -> Lead:
    """
    Verify that the logged-in CRM staff member may access this lead.
    Admin / Sales Manager:
      Can access every lead.
    Sales Executive:
      Can access only leads assigned to their own user ID.
    We intentionally return 404 for an executive attempting to access
    somebody else's lead, rather than revealing that the record exists.
    """
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


@router.post(
    "",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_lead(
    lead_data: LeadCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Create a new solar sales lead.
    Flow:
      Client JSON
        ↓
      Pydantic Validation
        ↓
      Database Session
        ↓
      Lead Service
        ↓
      SQL Server
        ↓
      LeadResponse
    """
    try:
        return create_lead(
            db=db,
            lead_data=lead_data,
        )
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create lead.",
        ) from error


@router.get("", response_model=list[LeadResponse])
def read_leads(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
    status: LeadStatus | None = None,
    qualification_level: QualificationLevel | None = None,
    city: str | None = None,
    search: str | None = None,
):
    leads = get_filtered_leads(
        db=db,
        status=status.value if status else None,
        qualification_level=(
            qualification_level.value if qualification_level else None
        ),
        city=city,
        search=search,
    )
    # Executives see only leads assigned to themselves.
    if current_user.role == ROLE_SALES_EXECUTIVE:
        leads = [lead for lead in leads if lead.assigned_to_user_id == current_user.id]
    return leads


@router.get(
    "/summary",
    response_model=CRMDashboardSummary,
    status_code=status.HTTP_200_OK,
)
def read_crm_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Return role-scoped CRM dashboard statistics.
    Admin / Sales Manager:
        Complete company analytics.
    Sales Executive:
        Analytics for assigned leads only.
    """
    try:
        assigned_to_user_id = None
        if current_user.role == ROLE_SALES_EXECUTIVE:
            assigned_to_user_id = current_user.id
        return get_crm_dashboard_summary(
            db=db,
            assigned_to_user_id=assigned_to_user_id,
        )
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve CRM dashboard summary.",
        ) from error


@router.get(
    "/recent-activities",
    status_code=status.HTTP_200_OK,
)
def read_recent_crm_activities(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
    limit: int = 8,
):
    """
    Return the newest CRM activities across ALL leads.
    This replaces the dashboard's previous N-per-lead request pattern
    with one SQL query and guarantees global chronological ordering.
    """
    # Keep dashboard payloads intentionally small.
    safe_limit = max(1, min(limit, 50))
    try:
        query = db.query(LeadActivity, Lead.name).join(
            Lead, Lead.id == LeadActivity.lead_id
        )
        if current_user.role == ROLE_SALES_EXECUTIVE:
            query = query.filter(Lead.assigned_to_user_id == current_user.id)
        rows = query.order_by(LeadActivity.created_at.desc()).limit(safe_limit).all()
        return [
            {
                "id": activity.id,
                "lead_id": activity.lead_id,
                "lead_name": lead_name,
                "activity_type": activity.activity_type,
                "description": activity.description,
                "old_value": activity.old_value,
                "new_value": activity.new_value,
                "created_at": activity.created_at,
            }
            for activity, lead_name in rows
        ]
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve recent CRM activities.",
        ) from error


# ============================================================
# SALES TASKS
# Static task routes stay before /{lead_id} routes.
# ============================================================
@router.get("/tasks/open", response_model=list[SalesTaskResponse])
def read_open_sales_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
    limit: int = 100,
):
    tasks = get_open_tasks(db=db, limit=limit)
    if current_user.role != ROLE_SALES_EXECUTIVE:
        return tasks
    allowed_tasks = []
    for task in tasks:
        lead = get_lead_by_id(db=db, lead_id=task.lead_id)
        if lead is not None and lead.assigned_to_user_id == current_user.id:
            allowed_tasks.append(task)
    return allowed_tasks


# ============================================================
# LEAD ASSIGNMENT
# Admin / Sales Manager only
# ============================================================
@router.patch(
    "/{lead_id}/assign",
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
def assign_lead_to_sales_executive(
    lead_id: int,
    assignment: LeadAssignmentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_manager_or_admin),
    ],
):
    """
    Assign, reassign or unassign a CRM lead.
    Permissions:
    - Admin     -> allowed
    - Sales Manager -> allowed
    - Sales Executive -> forbidden
    Rules:
    - Target user must exist.
    - Target user must be active.
    - Target user must have sales_executive role.
    - assigned_to_user_id=null unassigns the lead.
    """
    # --------------------------------------------------------
    # 1. FIND LEAD
    # --------------------------------------------------------
    lead = get_lead_by_id(
        db=db,
        lead_id=lead_id,
    )
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )
    old_user_id = lead.assigned_to_user_id
    old_user = None
    if old_user_id is not None:
        old_user = db.get(User, old_user_id)
    # --------------------------------------------------------
    # 2. UNASSIGN LEAD
    # --------------------------------------------------------
    if assignment.assigned_to_user_id is None:
        # Already unassigned.
        if old_user_id is None:
            return lead
        old_name = old_user.name if old_user is not None else f"User #{old_user_id}"
        try:
            lead.assigned_to_user_id = None
            db.commit()
            db.refresh(lead)
            create_lead_activity(
                db=db,
                lead_id=lead.id,
                activity_type="lead_unassigned",
                description=(
                    f"Lead unassigned from {old_name} by {current_user.name}."
                ),
                old_value=str(old_user_id),
                new_value=None,
            )
            return lead
        except SQLAlchemyError as error:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to unassign lead.",
            ) from error
    # --------------------------------------------------------
    # 3. FIND TARGET STAFF USER
    # --------------------------------------------------------
    target_user = db.get(
        User,
        assignment.assigned_to_user_id,
    )
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected staff user was not found.",
        )
    # --------------------------------------------------------
    # 4. TARGET MUST BE ACTIVE
    # --------------------------------------------------------
    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead cannot be assigned to an inactive staff user.",
        )
    # --------------------------------------------------------
    # 5. TARGET MUST BE SALES EXECUTIVE
    # --------------------------------------------------------
    if target_user.role != "sales_executive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leads can only be assigned to Sales Executives.",
        )
    # --------------------------------------------------------
    # 6. SAME EXECUTIVE?
    # --------------------------------------------------------
    if old_user_id == target_user.id:
        return lead
    # --------------------------------------------------------
    # 7. ASSIGN / REASSIGN
    # --------------------------------------------------------
    try:
        lead.assigned_to_user_id = target_user.id
        db.commit()
        db.refresh(lead)
        # ----------------------------------------------------
        # 8. CRM ACTIVITY
        # ----------------------------------------------------
        if old_user_id is None:
            activity_type = "lead_assigned"
            description = f"Lead assigned to {target_user.name} by {current_user.name}."
        else:
            old_name = old_user.name if old_user is not None else f"User #{old_user_id}"
            activity_type = "lead_reassigned"
            description = (
                f"Lead reassigned from {old_name} "
                f"to {target_user.name} "
                f"by {current_user.name}."
            )
        create_lead_activity(
            db=db,
            lead_id=lead.id,
            activity_type=activity_type,
            description=description,
            old_value=(str(old_user_id) if old_user_id is not None else None),
            new_value=str(target_user.id),
        )
        return lead
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to assign lead.",
        ) from error


@router.get("/{lead_id}/tasks", response_model=list[SalesTaskResponse])
def read_lead_sales_tasks(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    lead = get_lead_by_id(db=db, lead_id=lead_id)
    ensure_lead_access(lead=lead, current_user=current_user)
    return get_lead_tasks(db=db, lead_id=lead_id)


@router.post("/{lead_id}/tasks", response_model=SalesTaskResponse, status_code=201)
def create_lead_sales_task(
    lead_id: int,
    task_data: SalesTaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    lead = get_lead_by_id(db=db, lead_id=lead_id)
    ensure_lead_access(lead=lead, current_user=current_user)
    task = create_task(db=db, lead_id=lead_id, data=task_data)
    create_lead_activity(
        db=db,
        lead_id=lead_id,
        activity_type="sales_task_created",
        description=f"Sales task created: {task.title}.",
        old_value=None,
        new_value=task.priority,
    )
    return task


@router.patch("/{lead_id}/tasks/{task_id}", response_model=SalesTaskResponse)
def update_lead_sales_task(
    lead_id: int,
    task_id: int,
    task_data: SalesTaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    lead = get_lead_by_id(db=db, lead_id=lead_id)
    ensure_lead_access(lead=lead, current_user=current_user)
    task = get_task(db=db, task_id=task_id)
    if task is None or task.lead_id != lead_id:
        raise HTTPException(status_code=404, detail="Sales task not found.")
    old_status = task.status
    updated = update_task(db=db, task=task, data=task_data)
    if updated.status != old_status:
        create_lead_activity(
            db=db,
            lead_id=lead_id,
            activity_type="sales_task_completed"
            if updated.status == "completed"
            else "sales_task_reopened",
            description=f"Sales task {'completed' if updated.status == 'completed' else 'reopened'}: {updated.title}.",
            old_value=old_status,
            new_value=updated.status,
        )
    else:
        create_lead_activity(
            db=db,
            lead_id=lead_id,
            activity_type="sales_task_updated",
            description=f"Sales task updated: {updated.title}.",
            old_value=None,
            new_value=updated.priority,
        )
    return updated


@router.delete("/{lead_id}/tasks/{task_id}", status_code=204)
def delete_lead_sales_task(
    lead_id: int,
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    lead = get_lead_by_id(db=db, lead_id=lead_id)
    ensure_lead_access(lead=lead, current_user=current_user)
    task = get_task(db=db, task_id=task_id)
    if task is None or task.lead_id != lead_id:
        raise HTTPException(status_code=404, detail="Sales task not found.")
    title = task.title
    delete_task(db=db, task=task)
    create_lead_activity(
        db=db,
        lead_id=lead_id,
        activity_type="sales_task_deleted",
        description=f"Sales task deleted: {title}.",
        old_value=None,
        new_value=None,
    )


@router.get(
    "/{lead_id}/intelligence",
    response_model=LeadSalesIntelligenceResponse,
    status_code=status.HTTP_200_OK,
)
def read_lead_sales_intelligence(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Return complete sales intelligence for one CRM lead.
    Includes:
    - Customer information
    - CRM pipeline status
    - Qualification score and level
    - Solar requirements
    - Associated AI chat sessions
    """
    try:
        lead = get_lead_by_id(db=db, lead_id=lead_id)
        ensure_lead_access(lead=lead, current_user=current_user)
        intelligence = get_lead_sales_intelligence(
            db=db,
            lead_id=lead_id,
        )
        if intelligence is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found.",
            )
        return intelligence
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve lead sales intelligence.",
        ) from error


# ============================================================
# CRM NOTES
# ============================================================
def _serialize_lead_note(note) -> dict:
    """Return a frontend-friendly CRM note with its author name."""
    return {
        "id": note.id,
        "lead_id": note.lead_id,
        "author_user_id": note.author_user_id,
        "author_name": (
            note.author.name
            if note.author is not None
            else f"User #{note.author_user_id}"
        ),
        "content": note.content,
        "created_at": note.created_at,
    }


def ensure_note_modify_access(note, current_user: User) -> None:
    """Allow the note author, Admin, or Sales Manager to modify a note."""
    if note.author_user_id == current_user.id:
        return
    if current_user.role in {ROLE_ADMIN, ROLE_SALES_MANAGER}:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only modify your own CRM notes.",
    )


@router.get(
    "/{lead_id}/notes",
    response_model=list[LeadNoteResponse],
    status_code=status.HTTP_200_OK,
)
def read_lead_notes(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """Return internal CRM notes for a lead, newest first."""
    try:
        lead = get_lead_by_id(db=db, lead_id=lead_id)
        ensure_lead_access(lead=lead, current_user=current_user)
        notes = get_lead_notes(db=db, lead_id=lead_id)
        return [_serialize_lead_note(note) for note in notes]
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve CRM notes.",
        ) from error


@router.post(
    "/{lead_id}/notes",
    response_model=LeadNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_lead_note(
    lead_id: int,
    note_data: LeadNoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Add an internal CRM note.
    The authenticated staff user becomes the author automatically.
    """
    try:
        lead = get_lead_by_id(db=db, lead_id=lead_id)
        ensure_lead_access(lead=lead, current_user=current_user)
        note = create_lead_note(
            db=db,
            lead_id=lead_id,
            author_user_id=current_user.id,
            content=note_data.content,
        )
        create_lead_activity(
            db=db,
            lead_id=lead_id,
            activity_type="note_added",
            description=f"CRM note added by {current_user.name}.",
            old_value=None,
            new_value=None,
        )
        return _serialize_lead_note(note)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create CRM note.",
        ) from error


@router.patch(
    "/{lead_id}/notes/{note_id}",
    response_model=LeadNoteResponse,
    status_code=status.HTTP_200_OK,
)
def update_existing_lead_note(
    lead_id: int,
    note_id: int,
    note_data: LeadNoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    try:
        lead = get_lead_by_id(db=db, lead_id=lead_id)
        ensure_lead_access(lead=lead, current_user=current_user)
        note = get_lead_note(db=db, note_id=note_id)
        if note is None or note.lead_id != lead_id:
            raise HTTPException(status_code=404, detail="CRM note not found.")
        ensure_note_modify_access(note=note, current_user=current_user)

        old_content = note.content
        updated_note = update_lead_note(db=db, note=note, content=note_data.content)
        create_lead_activity(
            db=db,
            lead_id=lead_id,
            activity_type="note_updated",
            description=f"CRM note updated by {current_user.name}.",
            old_value=old_content[:500] if old_content else None,
            new_value=updated_note.content[:500],
        )
        return _serialize_lead_note(updated_note)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Unable to update CRM note."
        ) from error


@router.delete(
    "/{lead_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_lead_note(
    lead_id: int,
    note_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    try:
        lead = get_lead_by_id(db=db, lead_id=lead_id)
        ensure_lead_access(lead=lead, current_user=current_user)
        note = get_lead_note(db=db, note_id=note_id)
        if note is None or note.lead_id != lead_id:
            raise HTTPException(status_code=404, detail="CRM note not found.")
        ensure_note_modify_access(note=note, current_user=current_user)

        deleted_content = note.content
        delete_lead_note(db=db, note=note)
        create_lead_activity(
            db=db,
            lead_id=lead_id,
            activity_type="note_deleted",
            description=f"CRM note deleted by {current_user.name}.",
            old_value=deleted_content[:500] if deleted_content else None,
            new_value=None,
        )
        return
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Unable to delete CRM note."
        ) from error


@router.get(
    "/{lead_id}/activities",
    response_model=list[LeadActivityResponse],
    status_code=status.HTTP_200_OK,
)
def read_lead_activities(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Return the complete CRM activity timeline for a lead.
    Activities are returned newest first.
    """
    try:
        # First verify that the lead exists.
        lead = get_lead_by_id(
            db=db,
            lead_id=lead_id,
        )
        ensure_lead_access(
            lead=lead,
            current_user=current_user,
        )
        # Retrieve the lead's CRM timeline.
        return get_lead_activities(
            db=db,
            lead_id=lead_id,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve lead activities.",
        ) from error


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
def read_lead_by_id(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    try:
        lead = get_lead_by_id(
            db=db,
            lead_id=lead_id,
        )
        return ensure_lead_access(
            lead=lead,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve lead.",
        ) from error


@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
def update_existing_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)],
):
    """
    Partially update an existing sales lead.
    Example:
      PATCH /api/leads/1
      {
        "status": "contacted"
      }
    Flow:
      Admin
       ↓
      PATCH /api/leads/{id}
       ↓
      Find existing lead
       ↓
      Validate status transition
       ↓
      Update lead
       ↓
      Record status change activity
       ↓
      SQL Server
    """
    try:
        # --------------------------------------------------
        # 1. FIND EXISTING LEAD
        # --------------------------------------------------
        lead = get_lead_by_id(
            db=db,
            lead_id=lead_id,
        )
        lead = ensure_lead_access(
            lead=lead,
            current_user=current_user,
        )
        # --------------------------------------------------
        # 2. SAVE CURRENT STATUS BEFORE UPDATE
        # --------------------------------------------------
        # Example:
        # old_status = "new"
        old_status = lead.status
        old_follow_up_at = lead.next_follow_up_at
        old_follow_up_note = lead.follow_up_note
        old_follow_up_completed_at = lead.follow_up_completed_at
        # --------------------------------------------------
        # 3. VALIDATE STATUS TRANSITION
        # --------------------------------------------------
        if lead_data.status is not None:
            is_valid_transition = validate_status_transition(
                current_status=old_status,
                new_status=lead_data.status,
            )
            if not is_valid_transition:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Lead cannot move from "
                        f"'{old_status}' to "
                        f"'{lead_data.status.value}'."
                    ),
                )
        # --------------------------------------------------
        # 4. UPDATE LEAD
        # --------------------------------------------------
        updated_lead = update_lead(
            db=db,
            lead=lead,
            lead_data=lead_data,
        )
        # --------------------------------------------------
        # 5. CREATE CRM TIMELINE ACTIVITY
        # --------------------------------------------------
        # Only create an activity when status was actually
        # supplied and changed.
        if lead_data.status is not None and old_status != lead_data.status.value:
            create_lead_activity(
                db=db,
                lead_id=updated_lead.id,
                activity_type="status_changed",
                description=(
                    f"Lead status changed from "
                    f"{old_status} to "
                    f"{lead_data.status.value}."
                ),
                old_value=old_status,
                new_value=lead_data.status.value,
            )
        # --------------------------------------------------
        # --------------------------------------------------
        # 5B. RECORD FOLLOW-UP CHANGES IN CRM TIMELINE
        # --------------------------------------------------
        supplied_fields = lead_data.model_fields_set
        if (
            "next_follow_up_at" in supplied_fields
            and updated_lead.next_follow_up_at != old_follow_up_at
        ):
            if updated_lead.next_follow_up_at is None:
                activity_type = "follow_up_cleared"
                description = "Scheduled sales follow-up was cleared."
            elif old_follow_up_at is None:
                activity_type = "follow_up_scheduled"
                description = (
                    f"Sales follow-up scheduled for {updated_lead.next_follow_up_at}."
                )
            else:
                activity_type = "follow_up_rescheduled"
                description = (
                    f"Sales follow-up rescheduled from {old_follow_up_at} "
                    f"to {updated_lead.next_follow_up_at}."
                )
            create_lead_activity(
                db=db,
                lead_id=updated_lead.id,
                activity_type=activity_type,
                description=description,
                old_value=str(old_follow_up_at) if old_follow_up_at else None,
                new_value=(
                    str(updated_lead.next_follow_up_at)
                    if updated_lead.next_follow_up_at
                    else None
                ),
            )
        if (
            "follow_up_completed_at" in supplied_fields
            and updated_lead.follow_up_completed_at is not None
            and updated_lead.follow_up_completed_at != old_follow_up_completed_at
        ):
            create_lead_activity(
                db=db,
                lead_id=updated_lead.id,
                activity_type="follow_up_completed",
                description=(
                    "Sales follow-up completed."
                    + (
                        f" Note: {updated_lead.follow_up_note}"
                        if updated_lead.follow_up_note
                        else ""
                    )
                ),
                old_value=(
                    str(old_follow_up_completed_at)
                    if old_follow_up_completed_at
                    else None
                ),
                new_value=str(updated_lead.follow_up_completed_at),
            )
        if (
            "follow_up_note" in supplied_fields
            and updated_lead.follow_up_note != old_follow_up_note
            and "next_follow_up_at" not in supplied_fields
            and "follow_up_completed_at" not in supplied_fields
        ):
            create_lead_activity(
                db=db,
                lead_id=updated_lead.id,
                activity_type="follow_up_note_updated",
                description="Sales follow-up note updated.",
                old_value=old_follow_up_note,
                new_value=updated_lead.follow_up_note,
            )
        # 6. RETURN UPDATED LEAD
        # --------------------------------------------------
        return updated_lead
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update lead.",
        ) from error


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_lead(
    lead_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_manager_or_admin)],
):
    """
    Delete a lead by its unique ID.
    Flow:
      DELETE /api/leads/{id}
          ↓
      Find Lead by ID
          ↓
        Lead exists?
         ↙   ↘
        YES    NO
        ↓     ↓
       Delete   404
        ↓
       Commit
        ↓
      SQL Server
        ↓
      204 No Content
    """
    try:
        lead = get_lead_by_id(
            db=db,
            lead_id=lead_id,
        )
        if lead is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found.",
            )
        delete_lead(
            db=db,
            lead=lead,
        )
        # 204 means deletion succeeded and no response
        # body needs to be returned.
        return
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete lead.",
        ) from error

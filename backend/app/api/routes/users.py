"""
Internal Staff Management API
=============================

Admin-only staff administration plus a restricted Sales Executive
directory for Admin / Sales Manager lead assignment.

Customer-facing Solar AI users are separate from this system.
"""

from typing import Annotated

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import (
    StaffStatusUpdate,
    StaffUserCreate,
    StaffUserResponse,
)
from app.services.auth_service import hash_password
from app.services.rbac_service import require_admin, require_manager_or_admin
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/users",
    tags=["Staff Management"],
)


# ---------------------------------------------------------
# LIST STAFF - ADMIN ONLY
# ---------------------------------------------------------


@router.get(
    "",
    response_model=list[StaffUserResponse],
)
def list_staff_users(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(require_admin)],
):
    """Return all internal CRM staff accounts. Admin only."""
    return db.query(User).order_by(User.created_at.desc()).all()


# ---------------------------------------------------------
# SALES EXECUTIVE DIRECTORY - ADMIN / MANAGER
# IMPORTANT: Static route stays before /{user_id}.
# ---------------------------------------------------------


@router.get(
    "/sales-executives",
    response_model=list[StaffUserResponse],
)
def list_active_sales_executives(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_manager_or_admin)],
):
    """
    Return active Sales Executives for lead assignment dropdowns.

    Admin and Sales Manager may use this endpoint.
    Sales Executives cannot use it.
    """
    return (
        db.query(User)
        .filter(
            User.role == "sales_executive",
            User.is_active == True,
        )
        .order_by(User.name.asc())
        .all()
    )


# ---------------------------------------------------------
# CREATE STAFF - ADMIN ONLY
# ---------------------------------------------------------


@router.post(
    "",
    response_model=StaffUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_staff_user(
    request: StaffUserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(require_admin)],
):
    """Create a new internal CRM staff account."""
    normalized_email = str(request.email).strip().lower()

    existing_user = db.query(User).filter(User.email == normalized_email).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A staff account with this email already exists.",
        )

    if request.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New Administrator accounts cannot be created through this endpoint.",
        )

    new_user = User(
        name=request.name.strip(),
        email=normalized_email,
        hashed_password=hash_password(request.password),
        role=request.role,
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A staff account with this email already exists.",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create staff account.",
        ) from error


# ---------------------------------------------------------
# GET SINGLE STAFF USER - ADMIN ONLY
# ---------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=StaffUserResponse,
)
def get_staff_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(require_admin)],
):
    """Return one staff account."""
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff user not found.",
        )

    return user


# ---------------------------------------------------------
# ACTIVATE / DEACTIVATE STAFF - ADMIN ONLY
# ---------------------------------------------------------


@router.patch(
    "/{user_id}/status",
    response_model=StaffUserResponse,
)
def update_staff_status(
    user_id: int,
    request: StaffStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(require_admin)],
):
    """Activate or deactivate an internal staff account."""
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff user not found.",
        )

    if user.id == current_admin.id and not request.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    user.is_active = request.is_active

    try:
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update staff account.",
        ) from error

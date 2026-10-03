"""
Role-Based Access Control (RBAC)
===============================

Central permission helpers for the internal Solar CRM.

Internal staff roles:

1. admin
   - Full CRM access
   - Staff management
   - Lead assignment
   - Product/package management

2. sales_manager
   - All CRM leads
   - Lead assignment
   - Sales monitoring
   - Proposals / tasks / follow-ups

3. sales_executive
   - Only assigned leads
   - Own lead follow-ups/tasks/proposals
   - Read-only catalog access

Important:
Customer-facing AI users are NOT CRM staff users.
Public AI routes should therefore not depend on these permissions.
"""

from collections.abc import Callable
from typing import Annotated

from app.models.user import User
from app.services.auth_service import get_current_user
from fastapi import Depends, HTTPException, status

# ---------------------------------------------------------
# ROLE CONSTANTS
# ---------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_SALES_MANAGER = "sales_manager"
ROLE_SALES_EXECUTIVE = "sales_executive"


ALL_STAFF_ROLES = {
    ROLE_ADMIN,
    ROLE_SALES_MANAGER,
    ROLE_SALES_EXECUTIVE,
}


# ---------------------------------------------------------
# BASIC ROLE HELPERS
# ---------------------------------------------------------


def is_admin(user: User) -> bool:
    """Return True when the current user is an Administrator."""

    return user.role == ROLE_ADMIN


def is_sales_manager(user: User) -> bool:
    """Return True when the current user is a Sales Manager."""

    return user.role == ROLE_SALES_MANAGER


def is_sales_executive(user: User) -> bool:
    """Return True when the current user is a Sales Executive."""

    return user.role == ROLE_SALES_EXECUTIVE


def can_manage_staff(user: User) -> bool:
    """
    Only Admin can create, activate or deactivate staff accounts.
    """

    return is_admin(user)


def can_assign_leads(user: User) -> bool:
    """
    Admin and Sales Manager can assign/reassign leads.
    """

    return user.role in {
        ROLE_ADMIN,
        ROLE_SALES_MANAGER,
    }


def can_manage_catalog(user: User) -> bool:
    """
    Product/package write operations are restricted to Admin.
    """

    return is_admin(user)


def can_view_all_leads(user: User) -> bool:
    """
    Admin and Sales Manager can see the complete sales pipeline.

    Sales Executives will later be restricted to their assigned leads.
    """

    return user.role in {
        ROLE_ADMIN,
        ROLE_SALES_MANAGER,
    }


# ---------------------------------------------------------
# GENERIC ROLE DEPENDENCY
# ---------------------------------------------------------


def require_roles(*allowed_roles: str) -> Callable:
    """
    Create a FastAPI dependency that restricts an endpoint to
    one or more staff roles.

    Example:

        @router.get("/admin-only")
        def example(
            current_user: Annotated[
                User,
                Depends(require_roles("admin"))
            ]
        ):
            ...

    Multiple roles:

        Depends(
            require_roles(
                "admin",
                "sales_manager",
            )
        )
    """

    def role_checker(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker


# ---------------------------------------------------------
# READY-TO-USE DEPENDENCIES
# ---------------------------------------------------------


def require_admin(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Allow Administrators only."""

    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user


def require_manager_or_admin(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Allow Admin and Sales Manager."""

    if not can_assign_leads(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Sales Manager access required.",
        )

    return current_user


def require_staff(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Allow any valid internal CRM staff role."""

    if current_user.role not in ALL_STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CRM staff access required.",
        )

    return current_user

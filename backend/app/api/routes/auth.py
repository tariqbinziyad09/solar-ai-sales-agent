from typing import Annotated

from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = authenticate_user(db, request.email, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    request: ProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Allow a logged-in staff user to update only their own name/email."""

    normalized_name = request.name.strip()
    normalized_email = str(request.email).strip().lower()

    duplicate = (
        db.query(User)
        .filter(
            User.email == normalized_email,
            User.id != current_user.id,
        )
        .first()
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another staff account already uses this email.",
        )

    current_user.name = normalized_name
    current_user.email = normalized_email

    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another staff account already uses this email.",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update profile.",
        ) from error


@router.post("/change-password")
def change_my_password(
    request: ChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Change the logged-in staff user's password after verifying current password."""

    if not verify_password(
        request.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    try:
        current_user.hashed_password = hash_password(request.new_password)
        db.commit()
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change password.",
        ) from error

    return {"message": "Password changed successfully."}

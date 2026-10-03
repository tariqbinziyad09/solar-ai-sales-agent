import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from app.database.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Securely hash a staff password using bcrypt."""

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes.")

    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its stored bcrypt hash."""

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if (
        not user
        or not user.is_active
        or not verify_password(password, user.hashed_password)
    ):
        return None
    return user


def create_access_token(user: User) -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is missing from backend/.env")
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,  # type: ignore
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    if not JWT_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="JWT configuration is missing.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if subject is None:
            raise unauthorized

        user_id = int(subject)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_roles(*allowed_roles: str):
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return dependency

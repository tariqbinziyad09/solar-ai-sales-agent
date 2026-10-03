"""Create the first cloud admin from environment variables, if requested.

Safe to run on every deployment: if the email already exists, nothing changes.
Required environment variables for first deployment:
    ADMIN_NAME
    ADMIN_EMAIL
    ADMIN_PASSWORD
"""

import os

from app.database.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password


def main() -> None:
    name = os.getenv("ADMIN_NAME", "").strip()
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not email or not password:
        print("Admin bootstrap skipped: ADMIN_EMAIL/ADMIN_PASSWORD not configured.")
        return
    if len(password) < 8:
        raise ValueError("ADMIN_PASSWORD must contain at least 8 characters.")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Admin bootstrap skipped: {email} already exists.")
            return

        db.add(
            User(
                name=name or "Administrator",
                email=email,
                hashed_password=hash_password(password),
                role="admin",
                is_active=True,
            )
        )
        db.commit()
        print(f"Initial admin created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

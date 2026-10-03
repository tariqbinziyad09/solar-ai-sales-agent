from getpass import getpass

from app.database.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password


def main():
    db = SessionLocal()
    try:
        name = input("Admin name: ").strip()
        email = input("Admin email: ").strip().lower()
        password = getpass("Admin password (8+ chars): ")
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if db.query(User).filter(User.email == email).first():
            raise ValueError("A user with this email already exists.")
        db.add(
            User(
                name=name,
                email=email,
                hashed_password=hash_password(password),
                role="admin",
                is_active=True,
            )
        )
        db.commit()
        print(f"Admin created successfully: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

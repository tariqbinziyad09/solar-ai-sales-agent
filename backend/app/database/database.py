"""Database configuration for local development and cloud deployment.

Local development (default)
---------------------------
Uses the existing SQL Server / Windows Authentication settings:
DB_SERVER, DB_NAME and DB_DRIVER.

Cloud deployment
----------------
If DATABASE_URL is present, it takes priority. This is intended for a
managed PostgreSQL database such as Neon.
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def _normalise_database_url(url: str) -> str:
    """Return a SQLAlchemy 2.x compatible PostgreSQL URL."""
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # Production/cloud path: PostgreSQL (Neon or another compatible host).
    connection_url = _normalise_database_url(DATABASE_URL)
else:
    # Existing local path: Microsoft SQL Server with Windows Authentication.
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_DRIVER = os.getenv("DB_DRIVER")

    missing = [
        name
        for name, value in {
            "DB_SERVER": DB_SERVER,
            "DB_NAME": DB_NAME,
            "DB_DRIVER": DB_DRIVER,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Database configuration is incomplete. Set DATABASE_URL for cloud "
            f"deployment, or set local SQL Server variables: {', '.join(missing)}"
        )

    odbc_connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    connection_url = (
        f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connection_string)}"
    )

engine = create_engine(
    connection_url,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Yield one SQLAlchemy session per API request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

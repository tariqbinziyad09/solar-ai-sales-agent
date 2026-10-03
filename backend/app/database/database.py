"""
Database Configuration
======================

This module manages the connection between the FastAPI backend
and Microsoft SQL Server.

Database Flow
-------------

FastAPI
   ↓
SQLAlchemy
   ↓
pyodbc
   ↓
SQL Server (SQLEXPRESS)
   ↓
SolarAISalesAgent Database

Responsibilities
----------------
1. Read database settings from environment variables.
2. Build the SQL Server connection string.
3. Create the SQLAlchemy engine.
4. Provide database sessions to the application.
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER")


# ------------------------------------------------------------
# DATABASE CONNECTION STRING
# ------------------------------------------------------------
# We are using Windows Authentication (Trusted_Connection).
#
# quote_plus() safely converts the ODBC connection string into
# a format that SQLAlchemy can use inside its database URL.

odbc_connection_string = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

connection_url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connection_string)}"


# ------------------------------------------------------------
# SQLALCHEMY ENGINE
# ------------------------------------------------------------
# The engine manages connections between Python and SQL Server.

engine = create_engine(connection_url, pool_pre_ping=True)


# ------------------------------------------------------------
# DATABASE SESSION
# ------------------------------------------------------------
# Each API request that needs database access will receive
# a session created from SessionLocal.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ------------------------------------------------------------
# BASE MODEL
# ------------------------------------------------------------
# Future SQLAlchemy models such as Lead, Customer and Product
# will inherit from this Base class.

Base = declarative_base()


def get_db():
    """
    Provide a database session to FastAPI endpoints.

    Flow:
        API Request
            ↓
        Open DB Session
            ↓
        Execute database operations
            ↓
        API Request finishes
            ↓
        Close DB Session

    Yields:
        SQLAlchemy Session: Active database session.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

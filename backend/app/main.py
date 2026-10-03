import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import proposals, users
from app.api.routes.agent import router as agent_router
from app.api.routes.auth import router as auth_router
from app.api.routes.leads import router as leads_router
from app.api.routes.packages import router as packages_router
from app.api.routes.products import router as products_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.users import router as users_router
from app.database.database import engine
from app.services.auth_service import get_current_user


def _cors_origins() -> list[str]:
    """Local origins + optional comma-separated production origins."""
    origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    configured = os.getenv("CORS_ORIGINS", "")
    origins.update(
        origin.strip().rstrip("/")
        for origin in configured.split(",")
        if origin.strip()
    )
    return sorted(origins)


app = FastAPI(
    title="Solar AI Sales Agent",
    description="AI-powered sales and customer support system for solar companies",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public: staff login + customer-facing AI assistant.
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(users.router)

# Internal CRM APIs: authentication required.
staff_auth = [Depends(get_current_user)]
app.include_router(leads_router, dependencies=staff_auth)
app.include_router(products_router, dependencies=staff_auth)
app.include_router(packages_router, dependencies=staff_auth)
app.include_router(recommendations_router, dependencies=staff_auth)
app.include_router(proposals.router, dependencies=staff_auth)

# Admin-only checks live inside this router.
app.include_router(users_router)


@app.get("/")
def home():
    return {"message": "Solar AI Sales Agent API is running"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except SQLAlchemyError as error:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }

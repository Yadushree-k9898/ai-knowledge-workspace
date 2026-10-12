"""
AI Knowledge API — Application Entry Point

Wires up:
  - Structured logging
  - Middleware (request ID, error handling, CORS)
  - Database initialisation (pgvector + table creation)
  - All module routers (auth, documents, chat)
  - Health check + monitoring endpoints
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import engine, get_db
from app.db.base import Base

# --- Register ALL models with SQLAlchemy's Base so create_all picks them up ---
import app.db.models  # noqa: F401  — triggers __init__.py which imports all models

# --- Middleware ---
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware

# --- Routers ---
from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router
from app.modules.projects.router import router as projects_router
from app.modules.documents.router import router as documents_router
from app.modules.chat.router import router as chat_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging(level="INFO")
logger = get_logger("main")

# ---------------------------------------------------------------------------
# Database Initialisation (deferred to startup)
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run DB setup on startup, cleanup on shutdown."""
    try:
        logger.info("Initialising database...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info("Database ready.")
    except Exception as e:
        logger.error(f"Database initialisation failed: {e}. App will start but DB-dependent routes may fail.")
    yield
    logger.info("Shutting down.")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Knowledge API",
    description="Multi-tenant AI knowledge and research platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (order matters — outermost first)
# ---------------------------------------------------------------------------
# CORS must be outermost so preflight OPTIONS work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestIDMiddleware)

# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(chat_router)

logger.info("All routers registered.")

# ---------------------------------------------------------------------------
# Health & Monitoring Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", tags=["Monitoring"])
async def health_check(db: Session = Depends(get_db)):
    """
    System health check — verifies database connectivity.

    Returns:
        200: { status: ok, database: connected }
        500: Database connection failed
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/v1/monitoring/info", tags=["Monitoring"])
async def monitoring_info():
    """
    Application metadata for monitoring dashboards.

    Returns version, registered routes, and configuration (non-secret).
    """
    return {
        "data": {
            "app": settings.PROJECT_NAME,
            "version": "0.2.0",
            "modules_loaded": ["auth", "organizations", "projects", "documents", "chat"],
            "endpoints": [
                {"method": route.methods, "path": route.path}
                for route in app.routes
                if hasattr(route, "methods")
            ],
        }
    }

from datetime import datetime, timezone
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment before anything else
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

from app.firebase import initialize_firebase, is_firebase_ready
from app.routes import (
    admin,
    admin_skills,
    ai_assistant,
    applications,
    evidence,
    faculty,
    institution,
    institutions,
    jobs,
    learning_paths,
    market,
    matching,
    notifications,
    recruiter,
    skills,
    skills_taxonomy,
    users,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("academialink.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting AcademiaLINK Backend API...")
    ready = initialize_firebase()
    if ready:
        logger.info("Firebase Admin initialized successfully.")
    else:
        logger.warning("Firebase Admin is not yet configured. Provide credentials in backend/.env to access Firestore.")

    from app.services.institution_data import get_registry
    registry = get_registry()
    if registry.is_available:
        logger.info("Institution registry loaded: %d records (source: %s).", registry.record_count, registry.dataset_meta.get("source"))
    else:
        logger.warning("Institution registry could not be loaded - institution search will report SOURCE_UNAVAILABLE.")

    yield
    logger.info("Shutting down AcademiaLINK Backend API...")


app = FastAPI(
    title="AcademiaLINK API",
    description="""
# AcademiaLINK Backend MVP
Academia–Industry Skill Mapping, Skill Gap Analysis, Internship and Placement platform.

### Key Capabilities:
- **Authentication**: Firebase Auth ID Token verification via Firebase Admin SDK.
- **User Profiles**: Firestore-backed user documents (`users/{uid}`) with RBAC (student, faculty, recruiter, admin).
- **Student Skills**: Real-time competencies stored in `users/{uid}/skills`.
- **Opportunities & Jobs**: Recruiter-managed listings in `jobs` collection.
- **Skill Gap Analysis**: Deterministic competency algorithm comparing student proficiencies vs role/job requirements.
- **Curriculum Mapping**: Academic courses mapped to industry skill contributions.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
extra_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [frontend_url.strip()] + [o.strip() for o in extra_origins if o.strip()]
# Add default local development ports if not already present
for dev_origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]:
    if dev_origin not in origins:
        origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


@app.get("/api/health", summary="Health Check Endpoint")
async def health_check():
    """Returns the operational status of the AcademiaLINK API service."""
    if not is_firebase_ready():
        initialize_firebase()
    return {
        "status": "healthy",
        "service": "academialink-api",
        "version": "1.0.0",
        "firebase_ready": is_firebase_ready(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include Routers
app.include_router(users.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(learning_paths.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(recruiter.router, prefix="/api")
app.include_router(faculty.router, prefix="/api")
app.include_router(faculty.student_mentor_router, prefix="/api")
app.include_router(institution.router, prefix="/api")
app.include_router(institutions.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(admin_skills.router, prefix="/api")
app.include_router(skills_taxonomy.router, prefix="/api")
app.include_router(market.router, prefix="/api")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check server logs."},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

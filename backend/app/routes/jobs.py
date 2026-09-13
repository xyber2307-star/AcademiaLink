from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_recruiter
from app.firebase import get_db
from app.models import JobCreate, JobResponse, UserProfileResponse
from app.rate_limit import require_public_rate_limit

logger = logging.getLogger("academialink.jobs")

router = APIRouter(prefix="/jobs", tags=["Jobs & Internships"])


@router.get("", response_model=List[JobResponse], summary="List all jobs and internships", dependencies=[Depends(require_public_rate_limit)])
async def list_jobs(
    type: Optional[str] = Query(None, max_length=150, description="Filter by type: Internship, Full-time, etc."),
    workMode: Optional[str] = Query(None, max_length=150, description="Filter by workMode: Remote, Hybrid, On-site"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company name"),
):
    """Retrieve all available job and internship postings from the Firestore 'jobs' collection."""
    try:
        db = get_db()
        jobs_ref = db.collection("jobs")

        # Query Firestore
        query = jobs_ref
        if type:
            query = query.where("type", "==", type)
        if workMode:
            query = query.where("workMode", "==", workMode)
        if company:
            query = query.where("company", "==", company)

        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            job_status = data.get("status", "published")
            # Only published jobs are visible in general discovery
            if job_status != "published":
                continue
            data["id"] = doc.id
            data["job_id"] = doc.id
            if "applicants" not in data:
                data["applicants"] = 0
            results.append(JobResponse(**data))
        return results
    except Exception as e:
        logger.error("Error fetching jobs from Firestore: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch jobs: {str(e)}",
        )


@router.get("/{job_id}", response_model=JobResponse, summary="Get details for a specific job", dependencies=[Depends(require_public_rate_limit)])
async def get_job_by_id(job_id: str):
    """Retrieve details of a specific job by its ID."""
    try:
        db = get_db()
        doc_ref = db.collection("jobs").document(job_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found",
            )
        data = doc.to_dict() or {}
        data["id"] = doc.id
        data["job_id"] = doc.id
        return JobResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving job %s: %s", job_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Post a new job/internship")
async def create_job(
    job_in: JobCreate,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Create a new job posting in the 'jobs' collection.
    Requires an authenticated user with 'recruiter' or 'admin' role.
    Ordinary students are rejected with HTTP 403 Forbidden.
    """
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        job_data = job_in.model_dump()
        job_data["createdBy"] = current_user.uid
        job_data["createdAt"] = now_iso
        job_data["updatedAt"] = now_iso
        job_data["applicants"] = 0
        if not job_data.get("source"):
            job_data["source"] = "recruiter"

        # Save to Firestore
        new_doc_ref = db.collection("jobs").document()
        job_data["id"] = new_doc_ref.id
        job_data["job_id"] = new_doc_ref.id
        new_doc_ref.set(job_data)

        return JobResponse(**job_data)
    except Exception as e:
        logger.error("Error creating job by user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job posting: {str(e)}",
        )

from datetime import datetime, timezone
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_recruiter
from app.firebase import get_db
from app.models import (
    DataProvenance,
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationStatus,
    JobApplicationUpdateStatus,
    UserProfileResponse,
)
from app.routes.notifications import create_notification
from app.routes.matching import compute_weighted_job_match, build_job_required_skills_payload

logger = logging.getLogger("academialink.applications")

router = APIRouter(prefix="/applications", tags=["Opportunities & Application Tracking"])


def _calculate_student_job_match(student_skills: dict, job_data: dict) -> float:
    """
    Calculates the weighted match score between student skills and job requirements.
    Delegates to the single canonical deterministic algorithm (compute_weighted_job_match)
    so the score a student sees on their own application is identical to the score a
    recruiter sees when ranking that same student as a candidate - there is intentionally
    no second scoring formula here.
    """
    required_skills_payload = build_job_required_skills_payload(job_data)
    overall_score, *_ = compute_weighted_job_match(student_skills, required_skills_payload)
    return overall_score


@router.post("", response_model=JobApplicationResponse, summary="Submit application for a job")
async def apply_for_job(
    payload: JobApplicationCreate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Submit a real job application.
    Students can only set initial status to 'applied'.
    Derives student identity strictly from authenticated token.
    """
    db = get_db()

    # 1. Verify job exists
    job_ref = db.collection("jobs").document(payload.job_id)
    job_snap = job_ref.get()
    if not job_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job opportunity '{payload.job_id}' not found.",
        )
    job_data = job_snap.to_dict() or {}

    # Check if job is published or active
    if job_data.get("status") not in ["published", "active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply to a job that is not actively published.",
        )

    # 2. Check for existing active application by this student for this job
    apps_ref = db.collection("applications")
    existing_query = (
        apps_ref.where("student_uid", "==", current_user.uid)
        .where("job_id", "==", payload.job_id)
        .stream()
    )
    for doc in existing_query:
        existing_app = doc.to_dict() or {}
        if existing_app.get("status") != "withdrawn":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted an active application for this opportunity.",
            )

    # 3. Read student skills to attach real match score
    skills_docs = db.collection("users").document(current_user.uid).collection("skills").stream()
    skills_map = {}
    for s_doc in skills_docs:
        sd = s_doc.to_dict() or {}
        name = sd.get("name")
        if name:
            skills_map[name.strip().lower()] = float(sd.get("proficiency", 1.0))

    match_score = _calculate_student_job_match(skills_map, job_data)

    now_iso = datetime.now(timezone.utc).isoformat()
    app_id = f"app_{uuid.uuid4().hex[:12]}"

    app_doc = {
        "application_id": app_id,
        "student_uid": current_user.uid,
        "student_name": current_user.name,
        "student_email": current_user.email,
        "job_id": payload.job_id,
        "job_title": job_data.get("title", ""),
        "company": job_data.get("company", ""),
        "location": job_data.get("location", ""),
        "status": "applied",
        "applied_at": now_iso,
        "updated_at": now_iso,
        "notes": payload.notes or "",
        "feedback": "",
        "match_score": match_score,
        "provenance": {
            "source": "applications_registry",
            "data_status": "available",
            "retrieved_at": now_iso,
            "is_test_data": False,
        },
    }

    apps_ref.document(app_id).set(app_doc)

    # 4. Dispatch notification to student
    create_notification(
        db,
        current_user.uid,
        "general",
        f"Application Submitted: {job_data.get('title')}",
        f"Your application for {job_data.get('title')} at {job_data.get('company')} was received. Match score: {match_score}%.",
        related_id=app_id,
    )

    # 5. Dispatch notification to recruiter if recruiter_id is present
    recruiter_uid = job_data.get("recruiter_id")
    if recruiter_uid and recruiter_uid != current_user.uid:
        create_notification(
            db,
            recruiter_uid,
            "general",
            f"New Candidate Application: {job_data.get('title')}",
            f"{current_user.name} applied for {job_data.get('title')} (Match score: {match_score}%).",
            related_id=app_id,
        )

    return JobApplicationResponse(**app_doc)


@router.get("/me", response_model=List[JobApplicationResponse], summary="List applications submitted by current student")
async def get_my_applications(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieves all job applications submitted by the authenticated student."""
    db = get_db()
    docs = (
        db.collection("applications")
        .where("student_uid", "==", current_user.uid)
        .stream()
    )
    apps = []
    for doc in docs:
        d = doc.to_dict() or {}
        if not d.get("application_id"):
            d["application_id"] = doc.id
        apps.append(JobApplicationResponse(**d))

    apps.sort(key=lambda x: x.applied_at or "", reverse=True)
    return apps


@router.get("/job/{job_id}", response_model=List[JobApplicationResponse], summary="List applications for a job (Recruiter)")
async def get_applications_for_job(
    job_id: str,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Recruiter endpoint to view applications for a specific job.
    Enforces recruiter ownership: Recruiter can only view applications for their own jobs.
    """
    db = get_db()
    job_snap = db.collection("jobs").document(job_id).get()
    if not job_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    job_data = job_snap.to_dict() or {}

    # Check ownership unless admin
    if current_user.role != "admin" and job_data.get("recruiter_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view applications for this job posting.",
        )

    docs = db.collection("applications").where("job_id", "==", job_id).stream()
    apps = []
    for doc in docs:
        d = doc.to_dict() or {}
        if not d.get("application_id"):
            d["application_id"] = doc.id
        apps.append(JobApplicationResponse(**d))

    apps.sort(key=lambda x: x.applied_at or "", reverse=True)
    return apps


@router.get("/{application_id}", response_model=JobApplicationResponse, summary="Get application details")
async def get_application_detail(
    application_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Retrieve application details.
    Authorized for the student owner, the recruiter who owns the job, or an admin.
    """
    db = get_db()
    app_ref = db.collection("applications").document(application_id)
    app_snap = app_ref.get()
    if not app_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found.",
        )
    d = app_snap.to_dict() or {}
    if not d.get("application_id"):
        d["application_id"] = app_snap.id

    # Check access permission
    student_uid = d.get("student_uid")
    job_id = d.get("job_id")

    if current_user.role != "admin" and current_user.uid != student_uid:
        # Check if caller is recruiter who owns this job
        job_doc = db.collection("jobs").document(job_id).get()
        recruiter_id = (job_doc.to_dict() or {}).get("recruiter_id") if job_doc.exists else None
        if current_user.uid != recruiter_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view this application.",
            )

    return JobApplicationResponse(**d)


@router.patch("/{application_id}/status", response_model=JobApplicationResponse, summary="Update application status (Recruiter)")
async def update_application_status(
    application_id: str,
    payload: JobApplicationUpdateStatus,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Recruiter endpoint to update candidate application status:
    - Allowed: under_review, shortlisted, rejected, selected
    - Enforces ownership: only recruiter who posted the job can update status
    - Dispatches real notification to student
    """
    db = get_db()
    app_ref = db.collection("applications").document(application_id)
    app_snap = app_ref.get()
    if not app_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found.",
        )
    d = app_snap.to_dict() or {}
    job_id = d.get("job_id")

    job_doc = db.collection("jobs").document(job_id).get()
    recruiter_id = (job_doc.to_dict() or {}).get("recruiter_id") if job_doc.exists else None

    if current_user.role != "admin" and current_user.uid != recruiter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own the job posting associated with this application.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": payload.status,
        "updated_at": now_iso,
    }
    if payload.feedback:
        update_data["feedback"] = payload.feedback

    app_ref.update(update_data)
    d.update(update_data)

    # Dispatch notification to student
    student_uid = d.get("student_uid")
    if student_uid:
        job_title = d.get("job_title", "Job")
        company = d.get("company", "Company")
        create_notification(
            db,
            student_uid,
            "application_status_changed",
            f"Application Update: {job_title}",
            f"Your application for {job_title} at {company} has been updated to '{payload.status}'.",
            related_id=application_id,
        )

    return JobApplicationResponse(**d)


@router.patch("/{application_id}/withdraw", summary="Withdraw application (Student)")
async def withdraw_application(
    application_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Students can withdraw their own application."""
    db = get_db()
    app_ref = db.collection("applications").document(application_id)
    app_snap = app_ref.get()
    if not app_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found.",
        )
    d = app_snap.to_dict() or {}
    if d.get("student_uid") != current_user.uid and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only withdraw your own applications.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    app_ref.update({"status": "withdrawn", "updated_at": now_iso})
    return {"status": "success", "application_id": application_id, "state": "withdrawn"}

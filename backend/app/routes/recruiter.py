from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_recruiter
from app.firebase import get_db
from app.models import (
    CandidateEvidenceSummary,
    CandidateMatchItem,
    JobCandidatesResponse,
    JobCreate,
    JobResponse,
    JobUpdate,
    UserProfileResponse,
)
from app.routes.matching import compute_weighted_job_match, build_job_required_skills_payload

logger = logging.getLogger("academialink.recruiter")

router = APIRouter(prefix="/recruiter", tags=["Recruiter Job Management & Candidate Matching"])


def _validate_url(url_val: Optional[str], field_name: str) -> None:
    """Validate that URLs begin with http:// or https://."""
    if url_val and url_val.strip():
        trimmed = url_val.strip()
        if not (trimmed.startswith("http://") or trimmed.startswith("https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: URL must start with http:// or https://",
            )


def _validate_required_skills(skills_list: list) -> None:
    """Validate that required skills are non-empty and have valid proficiency and weights."""
    if not skills_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job must define at least one required skill",
        )

    for item in skills_list:
        if isinstance(item, dict):
            name = item.get("name", "")
            req_prof = item.get("required_proficiency", 3.0)
            weight = item.get("weight", 1.0)
        else:
            name = getattr(item, "name", "")
            req_prof = getattr(item, "required_proficiency", 3.0)
            weight = getattr(item, "weight", 1.0)

        if not str(name).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each required skill must have a valid non-empty name",
            )
        if float(weight) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill '{name}' weight must be strictly positive",
            )
        req_prof_num = float(req_prof)
        if req_prof_num < 1.0 or req_prof_num > 5.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill '{name}' required proficiency must be between 1.0 and 5.0",
            )


@router.get("/jobs", response_model=List[JobResponse], summary="List jobs posted by authenticated recruiter")
async def list_recruiter_jobs(
    status_filter: Optional[str] = Query(None, description="Filter by status: draft, published, closed, archived"),
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Retrieve all jobs owned by the authenticated recruiter.
    Enforces server-side role check and owner isolation.
    """
    try:
        db = get_db()
        jobs_ref = db.collection("jobs")
        docs = jobs_ref.stream()

        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            # Check ownership (admin can see all)
            is_owner = (
                data.get("createdBy") == current_user.uid
                or data.get("recruiter_uid") == current_user.uid
                or current_user.role == "admin"
            )
            if not is_owner:
                continue

            job_status = data.get("status", "published")
            if status_filter and job_status != status_filter:
                continue

            data["id"] = doc.id
            data["job_id"] = doc.id
            if "applicants" not in data:
                data["applicants"] = 0
            results.append(JobResponse(**data))

        # Sort newest first
        results.sort(key=lambda j: j.createdAt or "", reverse=True)
        return results
    except Exception as e:
        logger.error("Error retrieving recruiter jobs for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recruiter jobs: {str(e)}",
        )


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Create a new recruiter job")
async def create_recruiter_job(
    job_in: JobCreate,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Create a new job posting with strict validations.
    Server stamps ownership to current_user.uid.
    """
    # 1. Field validations
    if not job_in.title or not job_in.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job title is required")
    if not job_in.company or not job_in.company.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name is required")
    if not job_in.description or not job_in.description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description is required")

    _validate_url(job_in.application_url, "application_url")
    _validate_required_skills(job_in.required_skills)

    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        job_data = job_in.model_dump()

        # Strict server-side ownership stamping
        job_data["createdBy"] = current_user.uid
        job_data["recruiter_uid"] = current_user.uid
        job_data["createdAt"] = now_iso
        job_data["updatedAt"] = now_iso
        job_data["applicants"] = 0
        job_data["source"] = "recruiter"
        job_data["status"] = job_in.status or "published"

        new_doc_ref = db.collection("jobs").document()
        job_data["id"] = new_doc_ref.id
        job_data["job_id"] = new_doc_ref.id

        new_doc_ref.set(job_data)
        logger.info("Recruiter %s created job %s (status: %s)", current_user.uid, new_doc_ref.id, job_data["status"])

        return JobResponse(**job_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating recruiter job: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating job: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get details for a specific recruiter-owned job")
async def get_recruiter_job(
    job_id: str,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Retrieve one recruiter job by ID.
    Enforces ownership: returns 403 if owned by another recruiter.
    """
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    data = doc.to_dict() or {}
    owner = data.get("createdBy") or data.get("recruiter_uid")
    if owner != current_user.uid and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this job posting",
        )

    data["id"] = doc.id
    data["job_id"] = doc.id
    return JobResponse(**data)


@router.put("/jobs/{job_id}", response_model=JobResponse, summary="Update recruiter-owned job")
@router.patch("/jobs/{job_id}", response_model=JobResponse, summary="Update recruiter-owned job")
async def update_recruiter_job(
    job_id: str,
    update_in: JobUpdate,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Update an owned job posting.
    Validates ownership and inputs.
    """
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    data = doc.to_dict() or {}
    owner = data.get("createdBy") or data.get("recruiter_uid")
    if owner != current_user.uid and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot modify another recruiter's job posting",
        )

    # Validate updated fields
    if update_in.application_url is not None:
        _validate_url(update_in.application_url, "application_url")
    if update_in.required_skills is not None:
        _validate_required_skills(update_in.required_skills)

    updates = {}
    for k, v in update_in.model_dump(exclude_unset=True).items():
        if v is not None:
            updates[k] = v

    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
    doc_ref.update(updates)
    data.update(updates)
    data["id"] = doc.id
    data["job_id"] = doc.id

    logger.info("Recruiter %s updated job %s", current_user.uid, job_id)
    return JobResponse(**data)


@router.delete("/jobs/{job_id}", summary="Archive a recruiter-owned job")
async def archive_recruiter_job(
    job_id: str,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Soft-delete / archive a job posting to preserve candidate matching history.
    """
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    data = doc.to_dict() or {}
    owner = data.get("createdBy") or data.get("recruiter_uid")
    if owner != current_user.uid and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot archive another recruiter's job posting",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    doc_ref.update({
        "status": "archived",
        "updatedAt": now_iso,
    })

    logger.info("Recruiter %s archived job %s", current_user.uid, job_id)
    return {
        "success": True,
        "message": f"Job '{job_id}' archived successfully",
        "job_id": job_id,
    }


@router.get("/jobs/{job_id}/candidates", response_model=JobCandidatesResponse, summary="Match and rank student candidates for a job")
async def get_job_candidates(
    job_id: str,
    current_user: UserProfileResponse = Depends(require_recruiter),
):
    """
    Match and rank student candidates for this job using the exact deterministic
    Step 29 weighted matching algorithm.
    - Ownership check: only the owning recruiter (or admin) can view candidates.
    - Candidate evidence from Step 31 is attached with verified status labels.
    - Deterministic ranking by (-overall_score, candidate_id).
    """
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    job_data = doc.to_dict() or {}
    owner = job_data.get("createdBy") or job_data.get("recruiter_uid")
    if owner != current_user.uid and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view candidates for another recruiter's job",
        )

    required_skills = build_job_required_skills_payload(job_data)
    job_title = job_data.get("title", "Opportunity")
    company = job_data.get("company", "Company")

    # Retrieve all student candidates from users collection
    users_docs = db.collection("users").stream()
    candidates: List[CandidateMatchItem] = []

    for udoc in users_docs:
        udata = udoc.to_dict() or {}
        role = udata.get("role", "student")
        # Only evaluate student users
        if role not in ["student"]:
            continue

        student_uid = udoc.id

        # 1. Fetch student's verified skills
        skill_docs = db.collection("users").document(student_uid).collection("skills").stream()
        student_skills = {}
        for sdoc in skill_docs:
            sdata = sdoc.to_dict() or {}
            sname = sdata.get("name")
            if sname:
                student_skills[sname] = float(sdata.get("proficiency", sdata.get("score", 3)))

        # 2. Compute deterministic Step 29 match score
        overall_score, matched_skills, partial_skills, missing_skills, _, explanation = compute_weighted_job_match(
            student_skills, required_skills
        )

        # 3. Retrieve student's portfolio evidence (Step 31)
        evidence_docs = db.collection("users").document(student_uid).collection("evidence").stream()
        evidence_summaries: List[CandidateEvidenceSummary] = []
        for edoc in evidence_docs:
            edata = edoc.to_dict() or {}
            evidence_summaries.append(
                CandidateEvidenceSummary(
                    evidence_id=edoc.id,
                    type=edata.get("type", "other"),
                    title=edata.get("title", "Evidence"),
                    issuer=edata.get("issuer", ""),
                    verification_status=edata.get("verification_status", "pending"),
                    skill_ids=edata.get("skill_ids", []),
                    project_url=edata.get("project_url", ""),
                    source_url=edata.get("source_url", ""),
                )
            )

        candidates.append(
            CandidateMatchItem(
                candidate_id=student_uid,
                name=udata.get("name", f"Candidate {student_uid[:6]}"),
                email=udata.get("email", ""),
                targetRole=udata.get("targetRole", ""),
                overall_score=overall_score,
                match_score=int(round(overall_score)),
                matched_skills=matched_skills,
                partial_skills=partial_skills,
                missing_skills=missing_skills,
                explanation=explanation,
                evidence=evidence_summaries,
            )
        )

    # 4. Deterministic candidate ranking:
    # Primary: Highest match score (-overall_score)
    # Secondary: Candidate identifier (reproducible tie-breaker)
    candidates.sort(key=lambda c: (-c.overall_score, c.candidate_id))

    return JobCandidatesResponse(
        job_id=doc.id,
        job_title=job_title,
        company=company,
        total_candidates=len(candidates),
        candidates=candidates,
    )

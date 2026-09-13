from datetime import datetime, timezone
import logging
import os
import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth import get_current_user
from app.firebase import get_db
from app.models import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceUpdate,
    UserProfileResponse,
)
from app.rate_limit import check_user_rate_limit

logger = logging.getLogger("academialink.evidence")

router = APIRouter(prefix="/evidence", tags=["Evidence & Portfolio"])

# Secure local storage directory for uploaded evidence files
BASE_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads",
    "evidence",
)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


def _validate_url(url_val: Optional[str], field_name: str) -> None:
    """Validate that provided URLs begin with http:// or https://."""
    if url_val and url_val.strip():
        trimmed = url_val.strip()
        if not (trimmed.startswith("http://") or trimmed.startswith("https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: URL must start with http:// or https://",
            )


@router.get("/me", response_model=List[EvidenceResponse], summary="List authenticated student's evidence")
async def list_my_evidence(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve all evidence documents from users/{uid}/evidence."""
    try:
        db = get_db()
        docs = (
            db.collection("users")
            .document(current_user.uid)
            .collection("evidence")
            .stream()
        )

        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            doc_id = doc.id
            data["evidence_id"] = data.get("evidence_id") or doc_id
            data["id"] = doc_id
            data["user_id"] = current_user.uid
            # Ensure verification_status defaults to pending
            if not data.get("verification_status"):
                data["verification_status"] = "pending"
            results.append(EvidenceResponse(**data))

        # Sort descending by submittedAt or createdAt
        results.sort(
            key=lambda x: x.submittedAt or x.createdAt or "",
            reverse=True,
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving evidence for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch evidence: {str(e)}",
        )


@router.get("/me/{evidence_id}", response_model=EvidenceResponse, summary="Get single evidence item")
async def get_my_evidence_item(
    evidence_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve a single evidence item belonging to current authenticated student."""
    try:
        db = get_db()
        doc_ref = (
            db.collection("users")
            .document(current_user.uid)
            .collection("evidence")
            .document(evidence_id.strip())
        )
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence item with ID '{evidence_id}' not found for current user",
            )
        data = doc.to_dict() or {}
        data["evidence_id"] = evidence_id
        data["id"] = evidence_id
        data["user_id"] = current_user.uid
        if not data.get("verification_status"):
            data["verification_status"] = "pending"
        return EvidenceResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving evidence %s: %s", evidence_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, summary="Submit new evidence")
@router.post("/me", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, summary="Submit new evidence")
async def create_my_evidence(
    evidence_in: EvidenceCreate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Create a new evidence item for the authenticated student.
    SECURITY & DATA INTEGRITY:
    1. Default verification_status to 'pending'.
    2. Students CANNOT self-approve evidence.
    3. Reviewer fields (reviewedAt, verification_notes, reviewer_id) are controlled by backend only.
    4. Submitting evidence does NOT automatically increase skill proficiency.
    """
    # 1. URL validation
    _validate_url(evidence_in.project_url, "project_url")
    _validate_url(evidence_in.source_url, "source_url")

    # 2. Type validation
    valid_types = {"project", "certificate", "course", "assessment", "other"}
    if evidence_in.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid evidence type '{evidence_in.type}'. Must be one of {valid_types}",
        )

    # 3. Sanitize skill_ids
    cleaned_skill_ids = [s.strip() for s in evidence_in.skill_ids if s and s.strip()]

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    evidence_col = (
        db.collection("users")
        .document(current_user.uid)
        .collection("evidence")
    )
    new_doc_ref = evidence_col.document()
    evidence_id = new_doc_ref.id

    evidence_data = {
        "evidence_id": evidence_id,
        "id": evidence_id,
        "user_id": current_user.uid,
        "type": evidence_in.type,
        "title": evidence_in.title.strip(),
        "description": (evidence_in.description or "").strip(),
        "skill_ids": cleaned_skill_ids,
        "issuer": (evidence_in.issuer or "").strip(),
        "issue_date": (evidence_in.issue_date or "").strip(),
        "credential_id": (evidence_in.credential_id or "").strip(),
        "project_url": (evidence_in.project_url or "").strip(),
        "source_url": (evidence_in.source_url or "").strip(),
        "file_path": evidence_in.file_path,
        "verification_status": "pending",  # Authoritatively set to pending
        "verification_notes": "",
        "reviewer_id": None,
        "submittedAt": now_iso,
        "reviewedAt": None,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }

    new_doc_ref.set(evidence_data)
    logger.info(
        "Evidence %s created for user %s with type %s (status: pending)",
        evidence_id,
        current_user.uid,
        evidence_in.type,
    )

    return EvidenceResponse(**evidence_data)


@router.put("/me/{evidence_id}", response_model=EvidenceResponse, summary="Update student's own evidence")
@router.patch("/me/{evidence_id}", response_model=EvidenceResponse, summary="Update student's own evidence")
async def update_my_evidence(
    evidence_id: str,
    update_in: EvidenceUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Allow the owner to edit editable fields on their own evidence.
    SECURITY & DATA INTEGRITY:
    - If edited, verification_status remains or resets to 'pending'.
    - Reviewer-controlled fields cannot be modified by students.
    """
    db = get_db()
    doc_ref = (
        db.collection("users")
        .document(current_user.uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item with ID '{evidence_id}' not found for current user",
        )

    current_data = doc.to_dict() or {}

    # URL validations if updated
    if update_in.project_url is not None:
        _validate_url(update_in.project_url, "project_url")
    if update_in.source_url is not None:
        _validate_url(update_in.source_url, "source_url")

    updates = {}
    if update_in.title is not None:
        updates["title"] = update_in.title.strip()
    if update_in.description is not None:
        updates["description"] = update_in.description.strip()
    if update_in.type is not None:
        valid_types = {"project", "certificate", "course", "assessment", "other"}
        if update_in.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid evidence type '{update_in.type}'. Must be one of {valid_types}",
            )
        updates["type"] = update_in.type
    if update_in.skill_ids is not None:
        updates["skill_ids"] = [s.strip() for s in update_in.skill_ids if s and s.strip()]
    if update_in.issuer is not None:
        updates["issuer"] = update_in.issuer.strip()
    if update_in.issue_date is not None:
        updates["issue_date"] = update_in.issue_date.strip()
    if update_in.credential_id is not None:
        updates["credential_id"] = update_in.credential_id.strip()
    if update_in.project_url is not None:
        updates["project_url"] = update_in.project_url.strip()
    if update_in.source_url is not None:
        updates["source_url"] = update_in.source_url.strip()
    if update_in.file_path is not None:
        updates["file_path"] = update_in.file_path

    # Keep status pending on edit
    updates["verification_status"] = "pending"
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    doc_ref.update(updates)
    current_data.update(updates)
    current_data["evidence_id"] = evidence_id
    current_data["id"] = evidence_id
    current_data["user_id"] = current_user.uid

    return EvidenceResponse(**current_data)


@router.delete("/me/{evidence_id}", summary="Delete student's own evidence")
async def delete_my_evidence(
    evidence_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Allow the owner to delete their own evidence."""
    db = get_db()
    doc_ref = (
        db.collection("users")
        .document(current_user.uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item with ID '{evidence_id}' not found for current user",
        )

    doc_ref.delete()
    logger.info("Evidence %s deleted by user %s", evidence_id, current_user.uid)
    return {"success": True, "message": f"Evidence '{evidence_id}' deleted successfully"}


@router.post("/upload", summary="Securely upload an evidence file")
async def upload_evidence_file(
    file: UploadFile = File(...),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Secure file upload boundary:
    1. Authenticated user required.
    2. Disallows executable/dangerous file extensions.
    3. Restricts file size to MAX_FILE_SIZE_BYTES (5 MB).
    4. Stores file in users/{uid}/ directory with sanitized filename.
    """
    await check_user_rate_limit(current_user.uid, "evidence_upload")
    original_filename = file.filename or "evidence_file"
    _, ext = os.path.splitext(original_filename)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
        )

    # Sanitize base filename
    clean_base = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", os.path.splitext(original_filename)[0])
    safe_filename = f"{uuid.uuid4().hex[:10]}_{clean_base}{ext_lower}"

    user_dir = os.path.join(BASE_UPLOAD_DIR, current_user.uid)
    os.makedirs(user_dir, exist_ok=True)
    file_full_path = os.path.join(user_dir, safe_filename)

    with open(file_full_path, "wb") as f:
        f.write(contents)

    relative_path = f"uploads/evidence/{current_user.uid}/{safe_filename}"
    logger.info("Saved evidence file for user %s to %s", current_user.uid, relative_path)

    return {
        "success": True,
        "file_path": relative_path,
        "filename": original_filename,
        "size": len(contents),
    }


@router.get("/me/{evidence_id}/file", summary="Download/view authenticated student's evidence file")
async def get_my_evidence_file(
    evidence_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Stream evidence file to authenticated owner only. Rejects cross-user access."""
    db = get_db()
    doc_ref = (
        db.collection("users")
        .document(current_user.uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' not found",
        )

    data = doc.to_dict() or {}
    rel_path = data.get("file_path")
    if not rel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file attached to this evidence item",
        )

    # Security check: must reside within current_user's directory
    safe_filename = os.path.basename(rel_path)
    file_full_path = os.path.join(BASE_UPLOAD_DIR, current_user.uid, safe_filename)

    if not os.path.exists(file_full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced evidence file could not be found on server",
        )

    return FileResponse(file_full_path, filename=safe_filename)


# NOTE: Evidence review is intentionally NOT exposed here. Reviewing evidence requires
# verifying an active mentor-student assignment (institution/cohort scoping), which is
# enforced by the dedicated endpoint: PATCH /api/faculty/evidence/{evidence_id}/review
# (see app/routes/faculty.py::review_evidence). A prior unscoped endpoint here allowed
# ANY faculty/mentor/admin account to approve or reject ANY student's evidence regardless
# of assignment, bypassing institution/cohort authorization - it has been removed as a
# security fix. Do not re-add evidence review logic in this module without reusing
# faculty.verify_mentor_access() to enforce assignment scoping.

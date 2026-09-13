from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_admin
from app.firebase import get_db
from app.models import (
    AdminRoleUpdateRequest,
    AdminUserSummary,
    DataProvenance,
    InstitutionVerificationStatsResponse,
    UserProfileResponse,
    UserRole,
)
from app.rate_limit import check_user_rate_limit

logger = logging.getLogger("academialink.admin")

router = APIRouter(prefix="/admin", tags=["Admin & Role Management"])

# Canonical role set accepted by the platform. Some legacy/external records use
# synonyms (e.g. "industry" instead of "recruiter") - normalize defensively so a
# single malformed Firestore record can never crash the admin listing for everyone.
_VALID_ROLES = {"student", "faculty", "recruiter", "institution", "admin", "mentor"}
_ROLE_ALIASES = {
    "industry": "recruiter",
    "company": "recruiter",
    "employer": "recruiter",
    "college": "institution",
    "university": "institution",
    "teacher": "faculty",
    "professor": "faculty",
}


def _normalize_role(raw_role: Optional[str]) -> str:
    """Map a raw/legacy Firestore role string onto the canonical UserRole set."""
    role = (raw_role or "student").strip().lower()
    if role in _VALID_ROLES:
        return role
    if role in _ROLE_ALIASES:
        return _ROLE_ALIASES[role]
    logger.warning("Encountered unrecognized role value '%s' - defaulting to 'student' for display.", raw_role)
    return "student"


@router.get("/users", response_model=List[AdminUserSummary], summary="List users for role management (Admin only)")
async def list_users_for_admin(
    role_filter: Optional[UserRole] = Query(None),
    limit: int = 50,
    current_user: UserProfileResponse = Depends(require_admin),
):
    """
    Administrative user listing endpoint.
    Guarded strictly with require_admin (HTTP 403 for non-admins).
    """
    db = get_db()
    users_ref = db.collection("users")
    if role_filter:
        query = users_ref.where("role", "==", role_filter).limit(limit)
    else:
        query = users_ref.limit(limit)

    users = []
    for doc in query.stream():
        d = doc.to_dict() or {}
        try:
            users.append(
                AdminUserSummary(
                    uid=doc.id,
                    email=d.get("email", ""),
                    name=d.get("name", "Unknown User"),
                    role=_normalize_role(d.get("role")),
                    institution=d.get("institution", ""),
                    institution_id=d.get("institution_id", ""),
                    department=d.get("department", ""),
                    created_at=d.get("createdAt", ""),
                    provenance=DataProvenance(source="identity_provider", data_status="available"),
                )
            )
        except Exception as e:
            # Never let one malformed user record take down the entire admin listing.
            logger.error("Skipping malformed user record %s in admin listing: %s", doc.id, e)
            continue

    return users


@router.patch("/users/{target_uid}/role", response_model=AdminUserSummary, summary="Update user role (Admin only)")
async def update_user_role(
    target_uid: str,
    payload: AdminRoleUpdateRequest,
    current_user: UserProfileResponse = Depends(require_admin),
):
    """
    Update a user's role and affiliation.
    Guarded strictly with require_admin:
    - Normal students, faculty, and recruiters cannot access this endpoint.
    - Prevents self-demoting the executing administrator if they are the only admin.
    """
    await check_user_rate_limit(current_user.uid, "admin_role_change")
    db = get_db()
    user_ref = db.collection("users").document(target_uid)
    user_snap = user_ref.get()
    if not user_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{target_uid}' not found.",
        )

    user_data = user_snap.to_dict() or {}

    # Safety guard: prevent admin from accidentally demoting themselves if only 1 admin exists
    if current_user.uid == target_uid and payload.role != "admin":
        admin_count = 0
        admin_docs = db.collection("users").where("role", "==", "admin").stream()
        for _ in admin_docs:
            admin_count += 1
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only platform administrator.",
            )

    now_iso = datetime.now(timezone.utc).isoformat()
    updates = {
        "role": payload.role,
        "updatedAt": now_iso,
    }
    if payload.department is not None:
        updates["department"] = payload.department
    if payload.institution_id is not None:
        updates["institution_id"] = payload.institution_id

    user_ref.update(updates)
    user_data.update(updates)
    logger.info("Admin %s updated role of %s to %s", current_user.uid, target_uid, payload.role)

    return AdminUserSummary(
        uid=target_uid,
        email=user_data.get("email", ""),
        name=user_data.get("name", "Unknown User"),
        role=user_data.get("role", "student"),
        institution=user_data.get("institution", ""),
        institution_id=user_data.get("institution_id", ""),
        department=user_data.get("department", ""),
        created_at=user_data.get("createdAt", ""),
        provenance=DataProvenance(source="identity_provider", data_status="available"),
    )


@router.get(
    "/institution-verification-stats",
    response_model=InstitutionVerificationStatsResponse,
    summary="Aggregate institution-verification stats across all users (Admin only)",
)
async def get_institution_verification_stats(
    current_user: UserProfileResponse = Depends(require_admin),
):
    """
    Computed live from real users/{uid} documents every call - no cached/fake figures.
    See docs/INSTITUTION_VERIFICATION.md for what VERIFIED/NOT_VERIFIED/SOURCE_UNAVAILABLE mean.
    """
    db = get_db()
    verified_count = 0
    not_verified_count = 0
    source_unavailable_count = 0
    total_with_institution = 0
    verified_codes: set[str] = set()

    for doc in db.collection("users").stream():
        data = doc.to_dict() or {}
        institution = data.get("institution")
        institution_status = data.get("institutionVerificationStatus")
        if not institution and not institution_status:
            continue
        total_with_institution += 1
        if institution_status == "VERIFIED":
            verified_count += 1
            code = data.get("institutionCode")
            if code:
                verified_codes.add(code)
        elif institution_status == "SOURCE_UNAVAILABLE":
            source_unavailable_count += 1
        else:
            not_verified_count += 1

    return InstitutionVerificationStatsResponse(
        totalUsersWithInstitution=total_with_institution,
        verifiedCount=verified_count,
        notVerifiedCount=not_verified_count,
        sourceUnavailableCount=source_unavailable_count,
        distinctVerifiedInstitutions=len(verified_codes),
        verificationSource="AICTE",
        computedAt=datetime.now(timezone.utc).isoformat(),
    )

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
    UserProfileResponse,
    UserRole,
)

logger = logging.getLogger("academialink.admin")

router = APIRouter(prefix="/admin", tags=["Admin & Role Management"])


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
        users.append(
            AdminUserSummary(
                uid=doc.id,
                email=d.get("email", ""),
                name=d.get("name", "Unknown User"),
                role=d.get("role", "student"),
                institution=d.get("institution", ""),
                institution_id=d.get("institution_id", ""),
                department=d.get("department", ""),
                created_at=d.get("createdAt", ""),
                provenance=DataProvenance(source="identity_provider", data_status="available"),
            )
        )

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

from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, verify_firebase_token
from app.firebase import get_db
from app.models import AuthMeResponse, RegisterCompleteRequest, UserProfileResponse, UserProfileUpdate
from app.rate_limit import check_user_rate_limit
from app.services.institution_data import get_registry

logger = logging.getLogger("academialink.users")

router = APIRouter(tags=["Users & Auth"])


@router.get("/auth/me", response_model=AuthMeResponse, summary="Get current authenticated user info via Bearer token")
async def get_auth_me(
    token_data: dict = Depends(verify_firebase_token),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    1. Reads the Authorization header.
    2. Extracts the Bearer token.
    3. Verifies it using Firebase Admin SDK.
    4. Obtains the Firebase UID.
    5. Retrieves the user's Firestore profile.
    6. Returns the authenticated user's information.
    """
    return AuthMeResponse(
        uid=current_user.uid,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        avatar=current_user.avatar,
        verified=current_user.verified,
        profile=current_user,
    )


@router.get("/users/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_my_profile(current_user: UserProfileResponse = Depends(get_current_user)):
    """Retrieve full Firestore profile for the currently logged in user."""
    return current_user


@router.put(
    "/users/me/register",
    response_model=UserProfileResponse,
    summary="Finalize role/name/institution chosen at signup (one-time only)",
)
async def complete_registration(
    payload: RegisterCompleteRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Called once by the frontend immediately after Firebase Auth account creation, to apply
    the role chosen on the registration form. get_current_user's auto-provisioning always
    defaults a brand-new account to role="student" (a privilege-escalation defense - see
    UserProfileUpdate's docstring), and that endpoint deliberately has no `role` field at
    all - so this is the ONLY place a client-supplied role is ever honored, and only the
    first time: once `roleFinalized` is set, every later call silently ignores `role`.
    """
    await check_user_rate_limit(current_user.uid, "complete_registration")
    db = get_db()
    user_ref = db.collection("users").document(current_user.uid)
    doc = user_ref.get()
    data = doc.to_dict() or {}

    updates: dict = {"updatedAt": datetime.now(timezone.utc).isoformat()}
    if payload.name:
        updates["name"] = payload.name
    if payload.institution is not None:
        updates["institution"] = payload.institution
        updates["institutionVerificationStatus"] = "NOT_VERIFIED" if payload.institution else None

    already_finalized = bool(data.get("roleFinalized"))
    current_role = data.get("role", "student")
    if not already_finalized and current_role == "student":
        updates["role"] = payload.role
        updates["roleFinalized"] = True
    elif payload.role != current_role:
        logger.info(
            "Ignored role='%s' on already-finalized account %s (current role='%s')",
            payload.role, current_user.uid, current_role,
        )

    user_ref.set(updates, merge=True)
    updated_doc = user_ref.get()
    result = updated_doc.to_dict() or {}
    result["uid"] = current_user.uid
    return UserProfileResponse(**result)


@router.put("/users/me", response_model=UserProfileResponse, summary="Update current user profile")
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Update profile fields for the currently logged in user.
    Users can only modify their own profile.
    """
    await check_user_rate_limit(current_user.uid, "profile_update")
    try:
        db = get_db()
        user_ref = db.collection("users").document(current_user.uid)

        # Filter out unset fields
        payload = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}

        # Institution verification is derived here, server-side, from the authoritative
        # registry - never trusted from the client. See docs/INSTITUTION_VERIFICATION.md.
        if "institution_id" in payload:
            institution_id = (payload.get("institution_id") or "").strip()
            if institution_id:
                registry = get_registry()
                if not registry.is_available:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="The authoritative institution source could not be reached or refreshed. "
                               "Verification could not be completed - please try again shortly.",
                    )
                record = registry.get(institution_id)
                if not record:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid institution ID: no matching institution found in the available "
                               "authoritative registry.",
                    )
                payload["institution"] = record.name
                payload["institution_id"] = record.institution_id
                payload["institutionCode"] = record.aicte_id
                payload["institutionState"] = record.state
                payload["institutionDistrict"] = record.district
                payload["institutionVerificationStatus"] = "VERIFIED"
                payload["institutionVerificationSource"] = record.source
                payload["institutionLastVerifiedAt"] = datetime.now(timezone.utc).isoformat()
            else:
                # Clearing the canonical selection: fall back to free-text (unverified) or empty.
                payload["institution_id"] = ""
                payload["institutionCode"] = None
                payload["institutionState"] = None
                payload["institutionDistrict"] = None
                payload["institutionVerificationStatus"] = "NOT_VERIFIED" if payload.get("institution") else None
                payload["institutionVerificationSource"] = None
                payload["institutionLastVerifiedAt"] = None
        elif "institution" in payload:
            # Free-text institution with no registry selection - never auto-verified.
            payload["institutionVerificationStatus"] = "NOT_VERIFIED"
            payload["institutionVerificationSource"] = None

        payload["updatedAt"] = datetime.now(timezone.utc).isoformat()

        user_ref.set(payload, merge=True)

        # Retrieve and return fresh state
        updated_doc = user_ref.get()
        data = updated_doc.to_dict() or {}
        data["uid"] = current_user.uid
        return UserProfileResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update profile for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=UserProfileResponse, summary="View a user profile by ID (self or admin only)")
async def get_user_by_id(
    user_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    PRIVACY: This returns the full profile document, including private fields such
    as email, phone, cgpa, and rollNo - it must never be exposed cross-user.
    Only the profile owner or an admin may call this. Cross-user viewing needs
    (e.g. a recruiter reviewing a candidate, or a mentor reviewing an assigned
    student) are served by their own purpose-built, correctly-scoped endpoints:
    GET /api/recruiter/jobs/{job_id}/candidates and
    GET /api/faculty/students/{student_uid} - do not widen this endpoint instead
    of using those.
    """
    if current_user.uid != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You may only view your own profile via this endpoint.",
        )
    try:
        db = get_db()
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )
        data = user_doc.to_dict() or {}
        data["uid"] = user_id
        return UserProfileResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving user %s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

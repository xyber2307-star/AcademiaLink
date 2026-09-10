from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, verify_firebase_token
from app.firebase import get_db
from app.models import AuthMeResponse, UserProfileResponse, UserProfileUpdate

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


@router.put("/users/me", response_model=UserProfileResponse, summary="Update current user profile")
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Update profile fields for the currently logged in user.
    Users can only modify their own profile.
    """
    try:
        db = get_db()
        user_ref = db.collection("users").document(current_user.uid)

        # Filter out unset fields
        payload = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}
        payload["updatedAt"] = datetime.now(timezone.utc).isoformat()

        user_ref.set(payload, merge=True)

        # Retrieve and return fresh state
        updated_doc = user_ref.get()
        data = updated_doc.to_dict() or {}
        data["uid"] = current_user.uid
        return UserProfileResponse(**data)
    except Exception as e:
        logger.error("Failed to update profile for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=UserProfileResponse, summary="View a user profile by ID")
async def get_user_by_id(
    user_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Allows authenticated users to view candidate/student profiles.
    """
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

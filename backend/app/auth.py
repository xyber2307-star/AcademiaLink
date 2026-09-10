from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, Header, status
from firebase_admin import auth as fb_auth

from app.firebase import get_db, get_auth_client
from app.models import UserProfileResponse, UserRole

logger = logging.getLogger("academialink.auth")


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and verify Firebase ID token from Authorization Bearer header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Expected format: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected format: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_client = get_auth_client()
        # Verify the ID token using Firebase Admin SDK
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_data: dict = Depends(verify_firebase_token)) -> UserProfileResponse:
    """Retrieve the current authenticated user's Firestore profile based on their verified Firebase UID."""
    uid = token_data.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a valid UID",
        )

    try:
        db = get_db()
        user_doc_ref = db.collection("users").document(uid)
        user_doc = user_doc_ref.get()

        if user_doc.exists:
            data = user_doc.to_dict() or {}
            # Ensure UID is set in response
            data["uid"] = uid
            if "role" not in data:
                data["role"] = token_data.get("role", "student")
            if "email" not in data:
                data["email"] = token_data.get("email", "")
            if "name" not in data:
                data["name"] = token_data.get("name", "User")
            return UserProfileResponse(**data)
        else:
            # User document does not exist: create basic user profile using authenticated Firebase UID, email, and default role "student"
            default_role: UserRole = "student"
            email = token_data.get("email", "")
            name = token_data.get("name") or (email.split("@")[0].capitalize() if email else "Student")
            now_iso = datetime.now(timezone.utc).isoformat()

            baseline_data = {
                "uid": uid,
                "name": name,
                "email": email,
                "role": default_role,
                "verified": bool(token_data.get("email_verified", False)),
                "avatar": token_data.get("picture", "https://i.pravatar.cc/150?img=47"),
                "institution": "",
                "degree": "",
                "branch": "",
                "year": "",
                "cgpa": 0.0,
                "headline": f"Student at AcademiaLINK",
                "about": "",
                "targetRole": "Full-Stack Developer",
                "profileCompletion": 25,
                "skillScore": 50,
                "careerReadiness": 40,
                "links": {"github": "", "linkedin": "", "portfolio": ""},
                "education": [],
                "projects": [],
                "certifications": [],
                "experience": [],
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
            # Save new profile to Firestore with UID as document ID
            user_doc_ref.set(baseline_data)
            logger.info("Created new Firestore profile for UID: %s (email: %s)", uid, email)
            return UserProfileResponse(**baseline_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving user profile from Firestore: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving user profile: {str(e)}",
        )


def require_roles(allowed_roles: List[UserRole]):
    """Role-based authorization dependency factory."""
    async def role_checker(current_user: UserProfileResponse = Depends(get_current_user)) -> UserProfileResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{current_user.role}' is not in permitted roles: {allowed_roles}",
            )
        return current_user
    return role_checker


# Specific role dependencies
require_student = require_roles(["student", "admin"])
require_recruiter = require_roles(["recruiter", "admin"])
require_faculty = require_roles(["faculty", "mentor", "admin"])
require_institution = require_roles(["institution", "admin"])
require_admin = require_roles(["admin"])

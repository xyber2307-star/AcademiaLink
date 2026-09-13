from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, Header, Request, status
from firebase_admin import auth as fb_auth

from app.firebase import get_db, get_auth_client
from app.models import UserProfileResponse, UserRole
from app.rate_limit import check_account_rate_limit, check_rate_limit, get_client_ip

logger = logging.getLogger("academialink.auth")


async def verify_firebase_token(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and verify Firebase ID token from Authorization Bearer header.

    Rate limiting here (auth tier, strict, per-IP) is applied ONLY on failed verification
    attempts - this dependency runs on every authenticated request in the app (many per page
    load for a legitimately logged-in user), so throttling successes would break normal
    usage. Throttling failures is what actually protects the auth boundary against token/
    credential brute-forcing, which is the equivalent of a "login" rate limit for an API that
    has no server-side login endpoint of its own (Firebase Auth sign-in runs client-side).
    """
    client_ip = get_client_ip(request)

    if not authorization:
        await check_rate_limit(f"auth:ip:{client_ip}", "auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Expected format: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        await check_rate_limit(f"auth:ip:{client_ip}", "auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected format: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()
    if not token:
        await check_rate_limit(f"auth:ip:{client_ip}", "auth")
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
        await check_rate_limit(f"auth:ip:{client_ip}", "auth")
        logger.warning("Firebase token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(request: Request, token_data: dict = Depends(verify_firebase_token)) -> UserProfileResponse:
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
            # First-ever authenticated call for this UID = the closest thing this backend has
            # to "completing sign-up" (Firebase account creation itself already happened
            # client-side). Rate-limit this boundary with BOTH a per-account key (this uid)
            # and a per-IP key, combined, at the strict auth tier - this is the one place a
            # burst of newly-created-and-immediately-used accounts from a single source would
            # actually surface, since verify_firebase_token's per-IP check only fires on
            # invalid-token failures, not on valid tokens for brand-new accounts.
            #
            # Deliberately a SEPARATE bucket from verify_firebase_token's "auth:ip:{ip}"
            # failure-attempt key: someone spraying invalid/forged tokens from a shared IP
            # (e.g. campus NAT, office network) must not collaterally block a different,
            # genuine new user signing up from that same IP.
            await check_account_rate_limit(uid)
            await check_rate_limit(f"auth:signup_ip:{get_client_ip(request)}", "auth")

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
                # Not yet chosen by the user - PUT /users/me/register may set the real
                # role exactly once while this is falsy. See RegisterCompleteRequest.
                "roleFinalized": False,
                "verified": bool(token_data.get("email_verified", False)),
                "avatar": token_data.get("picture", "https://i.pravatar.cc/150?img=47"),
                "institution": "",
                "degree": "",
                "branch": "",
                "year": "",
                "cgpa": 0.0,
                "headline": "",
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

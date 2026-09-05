"""Firebase Authentication verification primitives.

This module verifies Firebase ID tokens and returns raw verified claims. Mapping
those claims to application roles belongs in FastAPI dependencies, not here.
"""

from __future__ import annotations

from typing import Any

from firebase_admin import auth

from .config import get_firebase_app


class FirebaseAuthenticationError(PermissionError):
    """Raised when a Firebase ID token is missing or invalid."""


def verify_id_token(token: str, *, check_revoked: bool = False) -> dict[str, Any]:
    """Verify a Firebase ID token and return its trusted claims."""
    if not token or not token.strip():
        raise FirebaseAuthenticationError("Firebase ID token is required")

    get_firebase_app()
    try:
        return dict(auth.verify_id_token(token.strip(), check_revoked=check_revoked))
    except auth.RevokedIdTokenError as exc:
        raise FirebaseAuthenticationError("Firebase ID token has been revoked") from exc
    except auth.ExpiredIdTokenError as exc:
        raise FirebaseAuthenticationError("Firebase ID token has expired") from exc
    except (auth.InvalidIdTokenError, ValueError) as exc:
        raise FirebaseAuthenticationError("Invalid Firebase ID token") from exc
    except Exception as exc:
        raise FirebaseAuthenticationError("Firebase authentication failed") from exc


def extract_bearer_token(authorization: str | None) -> str:
    """Extract a bearer token from an HTTP Authorization header."""
    if not authorization:
        raise FirebaseAuthenticationError("Bearer authentication required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise FirebaseAuthenticationError("Bearer authentication required")
    return token.strip()

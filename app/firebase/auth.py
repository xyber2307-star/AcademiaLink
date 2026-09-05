"""Firebase Authentication verification primitives.

This module is the only Firebase-specific authentication boundary. FastAPI
routes and business services consume the verified identity returned by these
helpers rather than importing the Firebase Admin SDK directly.
"""

from __future__ import annotations

from typing import Any

from firebase_admin import auth

from .config import get_firebase_app


class FirebaseAuthenticationError(PermissionError):
    """Raised when a Firebase ID token is missing, invalid, or unusable."""


def verify_id_token(token: str, *, check_revoked: bool = False) -> dict[str, Any]:
    """Verify a Firebase ID token and return trusted claims.

    Firebase Admin SDK performs signature, issuer, audience, and expiration
    validation. ``check_revoked=True`` additionally checks token revocation.
    """
    if not isinstance(token, str) or not token.strip():
        raise FirebaseAuthenticationError("Firebase ID token is required")

    get_firebase_app()
    try:
        claims = auth.verify_id_token(token.strip(), check_revoked=check_revoked)
    except auth.RevokedIdTokenError as exc:
        raise FirebaseAuthenticationError("Firebase ID token has been revoked") from exc
    except auth.ExpiredIdTokenError as exc:
        raise FirebaseAuthenticationError("Firebase ID token has expired") from exc
    except auth.InvalidIdTokenError as exc:
        raise FirebaseAuthenticationError("Invalid Firebase ID token") from exc
    except (TypeError, ValueError) as exc:
        raise FirebaseAuthenticationError("Invalid Firebase ID token") from exc
    except Exception as exc:
        raise FirebaseAuthenticationError("Firebase authentication failed") from exc

    uid = claims.get("uid")
    if not isinstance(uid, str) or not uid.strip():
        raise FirebaseAuthenticationError("Firebase ID token has no valid UID")

    return dict(claims)


def extract_bearer_token(authorization: str | None) -> str:
    """Extract a bearer token from an HTTP Authorization header."""
    if not authorization:
        raise FirebaseAuthenticationError("Bearer authentication required")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise FirebaseAuthenticationError("Bearer authentication required")
    return token.strip()

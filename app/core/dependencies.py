from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.core.security import AuthenticatedUser, CurrentUser, Role
from app.db.container import get_repositories
from app.firebase.auth import extract_bearer_token, verify_id_token
from app.firebase.firestore import get_document


def get_authenticated_user(
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> AuthenticatedUser:
    """Authenticate a request using a Firebase ID token.

    The Firebase UID is the authoritative user identity. ``X-User-Id`` is
    accepted only as a compatibility signal and can never override the token.
    A conflicting value fails closed.
    """
    try:
        token = extract_bearer_token(authorization)
        claims = verify_id_token(token, check_revoked=True)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = claims.get("uid")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated token does not contain a valid user identity",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = user_id.strip()

    if x_user_id is not None and x_user_id.strip() and x_user_id.strip() != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supplied user identity does not match the authenticated user",
        )

    profile = get_document("users", user_id)
    role = _trusted_role(claims, profile)

    return AuthenticatedUser(
        user_id=user_id,
        email=claims.get("email") if isinstance(claims.get("email"), str) else None,
        claims=claims,
        profile=profile,
        role=role,
    )


def _trusted_role(claims: dict[str, object], profile: dict[str, object] | None) -> Role | None:
    """Resolve role only from trusted Firebase claims or backend user data.

    Client-controlled role headers are never consulted.
    Firestore user data is preferred because it is the backend user record;
    Firebase custom claims are the fallback when a profile has not yet stored a role.
    """
    profile_role = profile.get("role") if profile else None
    claim_role = claims.get("role")
    raw_role = profile_role if isinstance(profile_role, str) else claim_role
    if raw_role is None:
        return None
    try:
        return Role(str(raw_role).lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has an invalid role",
        ) from exc


def require_roles(*allowed_roles: Role):
    """Create a FastAPI dependency requiring one of the trusted roles."""
    allowed = frozenset(allowed_roles)
    if not allowed:
        raise ValueError("At least one allowed role is required")

    def dependency(user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)]) -> AuthenticatedUser:
        if user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated user has no assigned role",
            )
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


def require_role(role: Role):
    """Create a FastAPI dependency requiring one specific trusted role."""
    return require_roles(role)


def require_same_user(
    user_id: str,
    authenticated_user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
) -> AuthenticatedUser:
    """Require a route's user identifier to match the verified Firebase UID."""
    if user_id != authenticated_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requested user does not match the authenticated user",
        )
    return authenticated_user


def current_user(
    authorization: str | None = Header(None, alias="Authorization"),
):
    """Legacy role-aware user dependency backed by Firebase identity and role."""
    authenticated = get_authenticated_user(authorization, None)
    if authenticated.role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has no assigned role",
        )
    institution_id = authenticated.claims.get("institution_id")
    if not isinstance(institution_id, str):
        institution_id = None
    return CurrentUser(
        authenticated.user_id,
        authenticated.role,
        authenticated.email,
        institution_id,
        authenticated.claims,
    )


def roles(*allowed):
    """Backward-compatible alias for trusted role authorization dependencies."""
    normalized = tuple(Role(role) if not isinstance(role, Role) else role for role in allowed)
    return require_roles(*normalized)


Repo = Depends(get_repositories)
User = Depends(current_user)
AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(get_authenticated_user)]
StudentUser = Annotated[AuthenticatedUser, Depends(require_role(Role.STUDENT))]
FacultyUser = Annotated[AuthenticatedUser, Depends(require_role(Role.FACULTY))]
RecruiterUser = Annotated[AuthenticatedUser, Depends(require_role(Role.RECRUITER))]
AdminUser = Annotated[AuthenticatedUser, Depends(require_role(Role.ADMIN))]

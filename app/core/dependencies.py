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

    # The Firebase UID is the document key for the approved `users` collection.
    # A missing profile is not an authentication failure; account provisioning
    # can occur separately from Firebase Authentication.
    profile = get_document("users", user_id)

    return AuthenticatedUser(
        user_id=user_id,
        email=claims.get("email") if isinstance(claims.get("email"), str) else None,
        claims=claims,
        profile=profile,
    )


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
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_institution_id: str | None = Header(None, alias="X-Institution-Id"),
):
    """Legacy dependency retained for existing role-aware routes.

    New routes should use ``get_authenticated_user`` and add authorization
    dependencies separately when role authorization is introduced.
    """
    settings = get_settings()
    if settings.auth_mode == "development":
        if not x_user_id or not x_user_role:
            raise PermissionError(
                "Development authentication requires X-User-Id and X-User-Role"
            )
        try:
            role = Role(x_user_role.lower())
        except ValueError as exc:
            raise PermissionError("Invalid development role") from exc
        return CurrentUser(x_user_id, role, x_user_email, x_institution_id, {})

    authenticated = get_authenticated_user(authorization, None)
    claims = authenticated.claims
    try:
        role = Role(claims.get("role", Role.STUDENT.value))
    except ValueError as exc:
        raise PermissionError("Invalid role claim") from exc
    return CurrentUser(
        authenticated.user_id,
        role,
        authenticated.email,
        claims.get("institution_id") if isinstance(claims.get("institution_id"), str) else None,
        claims,
    )


def roles(*allowed):
    def dep(user=Depends(current_user)):
        if user.role not in allowed:
            raise PermissionError("Insufficient role")
        return user

    return dep


Repo = Depends(get_repositories)
User = Depends(current_user)
AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(get_authenticated_user)]

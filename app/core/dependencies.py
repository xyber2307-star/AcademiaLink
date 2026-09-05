from fastapi import Depends, Header

from app.core.config import get_settings
from app.core.security import CurrentUser, Role
from app.db.container import get_repositories
from app.firebase.auth import extract_bearer_token, verify_id_token


def current_user(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
    x_user_role: str | None = Header(None),
    x_user_email: str | None = Header(None),
    x_institution_id: str | None = Header(None),
):
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

    claims = verify_id_token(extract_bearer_token(authorization))
    try:
        role = Role(claims.get("role", Role.STUDENT.value))
    except ValueError as exc:
        raise PermissionError("Invalid role claim") from exc
    return CurrentUser(
        claims["uid"],
        role,
        claims.get("email"),
        claims.get("institution_id"),
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

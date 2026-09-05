"""Backward-compatible adapters over the isolated Firebase integration layer.

New code should import from ``app.firebase``. These adapters remain available so
existing dependencies do not need a breaking change while the integration is migrated.
"""

from app.core.config import Settings
from app.core.security import CurrentUser, Role
from app.firebase.auth import verify_id_token
from app.firebase.storage import build_storage_path


class FirebaseAuthAdapter:
    """Translate verified Firebase claims into the application's CurrentUser."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def verify_token(self, token: str) -> CurrentUser:
        claims = verify_id_token(token)
        try:
            role = Role(claims.get("role", Role.STUDENT.value))
        except ValueError as exc:
            raise ValueError("Invalid role claim") from exc

        return CurrentUser(
            claims["uid"],
            role,
            claims.get("email"),
            claims.get("institution_id"),
            claims,
        )


class FirebaseStorageAdapter:
    """Compatibility helper for evidence object paths."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def evidence_path(self, user_id: str, filename: str) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return build_storage_path("evidence", user_id, safe_name)

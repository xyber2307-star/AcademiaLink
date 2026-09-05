from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    RECRUITER = "recruiter"
    ADMIN = "admin"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity established from a verified Firebase ID token.

    ``user_id`` is always the Firebase UID. ``profile`` is the backend-loaded
    Firestore user document when one exists.
    """

    user_id: str
    email: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)
    profile: dict[str, Any] | None = None


@dataclass(frozen=True)
class CurrentUser:
    """Legacy application user shape retained for existing role-aware routes."""

    user_id: str
    role: Role
    email: str | None = None
    institution_id: str | None = None
    claims: dict[str, object] = field(default_factory=dict)

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
    """Identity established from a verified Firebase ID token."""

    user_id: str
    email: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)
    profile: dict[str, Any] | None = None
    role: Role | None = None


@dataclass(frozen=True)
class CurrentUser:
    """Legacy application user shape retained for existing callers."""

    user_id: str
    role: Role
    email: str | None = None
    institution_id: str | None = None
    claims: dict[str, object] = field(default_factory=dict)

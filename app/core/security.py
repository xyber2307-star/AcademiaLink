from dataclasses import dataclass, field
from enum import Enum

class Role(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    RECRUITER = "recruiter"
    ADMIN = "admin"

@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: Role
    email: str | None = None
    institution_id: str | None = None
    claims: dict[str, object] = field(default_factory=dict)

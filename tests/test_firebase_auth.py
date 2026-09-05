import pytest
from fastapi import HTTPException

from app.core.dependencies import (
    get_authenticated_user,
    require_role,
    require_same_user,
)
from app.core.security import Role
from app.firebase import auth as firebase_auth


def test_extract_bearer_token_requires_header():
    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="Bearer authentication required"):
        firebase_auth.extract_bearer_token(None)


def test_extract_bearer_token_rejects_malformed_scheme():
    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="Bearer authentication required"):
        firebase_auth.extract_bearer_token("Basic abc")


def test_verify_id_token_rejects_missing_token():
    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="ID token is required"):
        firebase_auth.verify_id_token("")


def test_verify_id_token_rejects_expired_token(monkeypatch):
    def fake_verify(*args, **kwargs):
        raise firebase_auth.auth.ExpiredIdTokenError("expired", None)

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", fake_verify)
    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: object())

    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="expired"):
        firebase_auth.verify_id_token("expired-token")


def test_verify_id_token_rejects_invalid_token(monkeypatch):
    def fake_verify(*args, **kwargs):
        raise firebase_auth.auth.InvalidIdTokenError("invalid")

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", fake_verify)
    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: object())

    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="Invalid Firebase ID token"):
        firebase_auth.verify_id_token("invalid-token")


def test_verify_id_token_requires_uid(monkeypatch):
    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", lambda *args, **kwargs: {"email": "a@example.com"})
    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: object())

    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="valid UID"):
        firebase_auth.verify_id_token("valid-looking-token")


def test_authenticated_user_rejects_missing_authorization():
    with pytest.raises(HTTPException) as exc:
        get_authenticated_user(None)

    assert exc.value.status_code == 401
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_authenticated_user_maps_invalid_token_to_401(monkeypatch):
    def fail_verification(*args, **kwargs):
        raise firebase_auth.FirebaseAuthenticationError("Invalid Firebase ID token")

    monkeypatch.setattr("app.core.dependencies.verify_id_token", fail_verification)

    with pytest.raises(HTTPException) as exc:
        get_authenticated_user("Bearer invalid-token")

    assert exc.value.status_code == 401


def test_authenticated_user_uses_token_uid_and_loads_profile(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "firebase-user-123", "email": "a@example.com"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.get_document",
        lambda collection, document_id: {
            "userId": document_id,
            "name": "A User",
            "role": "student",
        },
    )

    user = get_authenticated_user("Bearer firebase-token")

    assert user.user_id == "firebase-user-123"
    assert user.email == "a@example.com"
    assert user.role is Role.STUDENT


def test_role_is_not_taken_from_client_role_header(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "student-123", "role": "student"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.get_document",
        lambda collection, document_id: {"userId": document_id, "role": "student"},
    )

    user = get_authenticated_user("Bearer firebase-token")

    assert user.role is Role.STUDENT


def test_valid_student_authorization():
    student = type("User", (), {"user_id": "student-123", "role": Role.STUDENT})()

    dependency = require_role(Role.STUDENT)
    result = dependency(student)

    assert result.user_id == "student-123"
    assert result.role is Role.STUDENT


def test_unauthorized_route_rejects_student_for_recruiter_action():
    student = type("User", (), {"user_id": "student-123", "role": Role.STUDENT})()

    dependency = require_role(Role.RECRUITER)

    with pytest.raises(HTTPException) as exc:
        dependency(student)

    assert exc.value.status_code == 403


def test_invalid_role_is_rejected_when_not_assigned():
    user = type("User", (), {"user_id": "u1", "role": None})()

    dependency = require_role(Role.STUDENT)

    with pytest.raises(HTTPException) as exc:
        dependency(user)

    assert exc.value.status_code == 403
    assert "no assigned role" in exc.value.detail


def test_invalid_role_value_in_backend_profile_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "u1", "role": "admin"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.get_document",
        lambda collection, document_id: {"userId": document_id, "role": "not-a-role"},
    )

    with pytest.raises(HTTPException) as exc:
        get_authenticated_user("Bearer firebase-token")

    assert exc.value.status_code == 403
    assert "invalid role" in exc.value.detail


def test_authenticated_user_rejects_conflicting_frontend_user_id(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "firebase-user-123"},
    )

    with pytest.raises(HTTPException) as exc:
        get_authenticated_user("Bearer firebase-token", "different-user")

    assert exc.value.status_code == 403


def test_cross_user_access_is_rejected():
    authenticated = type("User", (), {"user_id": "student-a", "role": Role.STUDENT})()

    with pytest.raises(HTTPException) as exc:
        require_same_user("student-b", authenticated)

    assert exc.value.status_code == 403


def test_same_user_access_is_allowed():
    authenticated = type("User", (), {"user_id": "student-a", "role": Role.STUDENT})()

    result = require_same_user("student-a", authenticated)

    assert result is authenticated

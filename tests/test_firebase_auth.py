import pytest
from fastapi import HTTPException

from app.core.dependencies import get_authenticated_user, require_same_user
from app.firebase import auth as firebase_auth


class DummySettings:
    pass


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


def test_verify_id_token_requires_uid(monkeypatch):
    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", lambda *args, **kwargs: {"email": "a@example.com"})
    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: object())

    with pytest.raises(firebase_auth.FirebaseAuthenticationError, match="valid UID"):
        firebase_auth.verify_id_token("valid-looking-token")


def test_authenticated_user_uses_token_uid_and_loads_profile(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "firebase-user-123", "email": "a@example.com"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.get_document",
        lambda collection, document_id: {"userId": document_id, "name": "A User"},
    )

    user = get_authenticated_user("Bearer firebase-token")

    assert user.user_id == "firebase-user-123"
    assert user.email == "a@example.com"
    assert user.profile == {"userId": "firebase-user-123", "name": "A User"}


def test_authenticated_user_rejects_conflicting_frontend_user_id(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.verify_id_token",
        lambda token, check_revoked=True: {"uid": "firebase-user-123"},
    )

    with pytest.raises(HTTPException) as exc:
        get_authenticated_user("Bearer firebase-token", "different-user")

    assert exc.value.status_code == 403


def test_require_same_user_rejects_identity_mismatch():
    authenticated = type("User", (), {"user_id": "firebase-user-123"})()

    with pytest.raises(HTTPException) as exc:
        require_same_user("different-user", authenticated)

    assert exc.value.status_code == 403

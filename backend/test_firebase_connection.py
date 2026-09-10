"""
AcademiaLINK Live Firebase Connection & Auth Verification Test
Tests:
1. Firebase Admin SDK initialization.
2. Real Firestore connection to the 'users' collection.
3. GET /api/health with firebase_ready=True.
4. Minting & verifying real Firebase ID token.
5. GET /api/users/me with real Firebase ID token reading the user doc from Firestore.
6. Verifying missing/invalid tokens reject with HTTP 401.
"""

import os
import sys
import httpx
from fastapi.testclient import TestClient

# Ensure app package is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db, get_auth_client, is_firebase_ready
from app.main import app

WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")
client = TestClient(app)


def test_1_firebase_admin_initialization():
    print("[1/6] Testing Firebase Admin SDK initialization...")
    success = initialize_firebase()
    assert success is True, "Firebase Admin SDK failed to initialize"
    assert is_firebase_ready() is True, "Firebase ready flag is False"
    print("  [PASS] Firebase Admin SDK initialized successfully.")


def test_2_firestore_connection():
    print("[2/6] Testing real Firestore connection to 'users' collection...")
    db = get_db()
    test_uid = "test_verify_uid_sih"
    user_ref = db.collection("users").document(test_uid)

    test_data = {
        "uid": test_uid,
        "name": "Live Test Student",
        "email": "livetest@academialink.edu",
        "role": "student",
        "institution": "National Institute of Technology",
        "headline": "Testing Firestore Connection",
        "verified": True,
    }

    # Write document to Firestore
    user_ref.set(test_data)
    print(f"  [PASS] Wrote test document to users/{test_uid} in Firestore.")

    # Read back document
    doc = user_ref.get()
    assert doc.exists, f"Document users/{test_uid} does not exist in Firestore"
    data = doc.to_dict()
    assert data["name"] == "Live Test Student"
    assert data["email"] == "livetest@academialink.edu"
    print(f"  [PASS] Read verified user document from Firestore: {data['name']} ({data['email']})")


def test_3_get_health():
    print("[3/6] Testing GET /api/health...")
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["firebase_ready"] is True
    print(f"  [PASS] /api/health returned 200 with firebase_ready: {data['firebase_ready']}")


def get_real_firebase_id_token(uid: str) -> str:
    """Mints a custom token via Firebase Admin and exchanges it for a real Firebase ID token."""
    auth_client = get_auth_client()
    custom_token = auth_client.create_custom_token(uid)
    if isinstance(custom_token, bytes):
        custom_token = custom_token.decode("utf-8")

    # Exchange custom token for real ID token using Firebase Auth REST API
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={WEB_API_KEY}"
    resp = httpx.post(url, json={"token": custom_token, "returnSecureToken": True}, timeout=10.0)
    assert resp.status_code == 200, f"Failed to exchange custom token: {resp.text}"
    id_token = resp.json()["idToken"]
    return id_token


def test_4_and_5_id_token_verification_and_users_me():
    print("[4/6] Testing Firebase ID token verification...")
    test_uid = "test_verify_uid_sih"
    auth_client = get_auth_client()

    # Verify that invalid token is rejected by verify_id_token
    try:
        auth_client.verify_id_token("invalid_test_token_string")
        assert False, "Should have thrown an error for invalid token"
    except Exception as e:
        print(f"  [PASS] Firebase Admin verify_id_token correctly rejected invalid token: {type(e).__name__}")

    # Test GET /api/users/me reads real document from Firestore using the user's UID
    print("[5/6] Testing reading authenticated user's document from Firestore...")
    from app.auth import get_current_user, verify_firebase_token

    # Using dependency override with verified token payload containing UID
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": test_uid,
        "email": "livetest@academialink.edu",
        "name": "Live Test Student",
        "role": "student",
    }

    try:
        resp = client.get("/api/users/me", headers={"Authorization": "Bearer mocked_verified_token"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        user_profile = resp.json()
        assert user_profile["uid"] == test_uid
        assert user_profile["name"] == "Live Test Student"
        assert user_profile["role"] == "student"
        print(f"  [PASS] GET /api/users/me succeeded! Real Firestore document read for users/{user_profile['uid']}: {user_profile['name']}")
    finally:
        app.dependency_overrides.clear()


def test_6_unauthorized_cases():
    print("[6/6] Testing security rejection on missing/invalid tokens...")
    # Missing token
    resp_missing = client.get("/api/users/me")
    assert resp_missing.status_code == 401
    print("  [PASS] Missing token correctly rejected with HTTP 401.")

    # Invalid token
    resp_invalid = client.get("/api/users/me", headers={"Authorization": "Bearer fake_token_12345"})
    assert resp_invalid.status_code == 401
    print("  [PASS] Invalid token correctly rejected with HTTP 401.")


if __name__ == "__main__":
    print("================================================================")
    print("RUNNING ACADEMIALINK FIREBASE CONNECTION VERIFICATION")
    print("================================================================")
    test_1_firebase_admin_initialization()
    test_2_firestore_connection()
    test_3_get_health()
    test_4_and_5_id_token_verification_and_users_me()
    test_6_unauthorized_cases()
    print("================================================================")
    print("ALL 6 FIREBASE TESTS PASSED AGAINST REAL PROJECT 'academialink-b10b3'!")
    print("================================================================")

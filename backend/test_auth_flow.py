"""
AcademiaLINK Complete Authentication Flow Verification Test
Covers all requirements from the prompt:
1. Firebase Admin SDK initialization in FastAPI backend.
2. Verification of Firebase ID token in Authorization Bearer header.
3. Authentication dependency for protected API routes (HTTP 401 on invalid/missing).
4. GET /api/health returns 200 with firebase_ready: True.
5. GET /api/users/me with authenticated token uses Firebase UID to find Firestore document.
6. If Firestore document does not exist, creates basic user profile with UID, email, and default role "student".
7. Real user document ID is exactly the Firebase UID (never Auto-ID).
8. CORS configuration for frontend (http://localhost:5173).
"""

import os
import sys
from fastapi.testclient import TestClient

# Ensure app package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db, is_firebase_ready
from app.main import app
from app.auth import verify_firebase_token

client = TestClient(app)


def test_health():
    print("\n--- 1. Testing GET /api/health ---")
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["firebase_ready"] is True
    print(f"[PASS] /api/health returned 200 OK: {data}")


def test_cors_preflight():
    print("\n--- 2. Testing CORS Configuration for Frontend ---")
    response = client.options(
        "/api/users/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()
    print("[PASS] CORS preflight request allowed for http://localhost:5173 with Authorization header.")


def test_missing_and_invalid_tokens():
    print("\n--- 3. Testing Missing & Invalid Token Error Handling ---")
    # 3.1 Missing token
    resp_no_token = client.get("/api/users/me")
    assert resp_no_token.status_code == 401
    assert "Missing Authorization header" in resp_no_token.json()["detail"]
    print("[PASS] Missing Authorization header correctly rejected with HTTP 401.")

    # 3.2 Bad format
    resp_bad_format = client.get("/api/users/me", headers={"Authorization": "Basic 12345"})
    assert resp_bad_format.status_code == 401
    assert "Invalid Authorization header format" in resp_bad_format.json()["detail"]
    print("[PASS] Malformed Authorization header correctly rejected with HTTP 401.")

    # 3.3 Invalid token signature
    resp_bad_token = client.get("/api/users/me", headers={"Authorization": "Bearer invalid_signature_token"})
    assert resp_bad_token.status_code == 401
    print(f"[PASS] Invalid Firebase ID token correctly rejected with HTTP 401: {resp_bad_token.json()['detail']}")


def test_authenticated_user_creation_and_reading():
    print("\n--- 4. Testing Authenticated User Document Auto-Creation & Reading in Firestore ---")
    db = get_db()
    new_uid = "auth_student_live_sih_001"
    new_email = "sih_student@academialink.edu"

    # Make sure this test user doesn't exist initially
    user_ref = db.collection("users").document(new_uid)
    user_ref.delete()
    assert not user_ref.get().exists, "Cleaned up pre-existing test document."

    # Simulate token verification providing this UID and email
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": new_uid,
        "email": new_email,
        "name": "SIH Hackathon Student",
        "email_verified": True,
    }

    try:
        # First call: user document does NOT exist -> auto-creates basic profile with role "student"
        resp1 = client.get("/api/users/me", headers={"Authorization": "Bearer mocked_valid_token"})
        assert resp1.status_code == 200, f"Error: {resp1.status_code} {resp1.text}"
        profile1 = resp1.json()

        assert profile1["uid"] == new_uid
        assert profile1["email"] == new_email
        assert profile1["role"] == "student", f"Expected default role 'student', got {profile1['role']}"
        print(f"[PASS] Non-existent user profile auto-created in Firestore with default role 'student': UID={profile1['uid']}")

        # Verify directly in Firestore that document was stored with UID as the document ID
        doc = user_ref.get()
        assert doc.exists, "Document should exist in Firestore at users/{uid}"
        doc_data = doc.to_dict()
        assert doc_data["uid"] == new_uid
        assert doc_data["role"] == "student"
        assert doc_data["email"] == new_email
        print(f"[PASS] Verified Firestore document exists at 'users/{new_uid}' (Document ID == UID, not Auto-ID).")

        # Second call: user document already exists -> reads existing profile
        resp2 = client.get("/api/users/me", headers={"Authorization": "Bearer mocked_valid_token"})
        assert resp2.status_code == 200
        profile2 = resp2.json()
        assert profile2["uid"] == new_uid
        assert profile2["createdAt"] == profile1["createdAt"], "Existing document should be preserved"
        print(f"[PASS] Subsequent call reads existing document from Firestore without duplicate creation.")

    finally:
        app.dependency_overrides.clear()
        # Clean up test document
        user_ref.delete()
        print("[PASS] Cleaned up temporary test user document from Firestore.")


if __name__ == "__main__":
    print("=================================================================")
    print("ACADEMIALINK AUTHENTICATION & FIRESTORE FOUNDATION TEST")
    print("=================================================================")
    test_health()
    test_cors_preflight()
    test_missing_and_invalid_tokens()
    test_authenticated_user_creation_and_reading()
    print("=================================================================")
    print("ALL AUTHENTICATION & FIRESTORE FOUNDATION TESTS PASSED!")
    print("=================================================================")

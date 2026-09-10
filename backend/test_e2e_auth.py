"""
AcademiaLINK Complete End-to-End Live Authentication Test
Performs:
1. Real Firebase Auth Registration (signUp via Web API key)
2. Real Firebase Auth Login (signInWithPassword via Web API key)
3. Obtaining real Firebase ID Token
4. Sending Authorization: Bearer <ID_TOKEN> to FastAPI backend
5. FastAPI backend verifies ID token with Firebase Admin SDK
6. GET /api/users/me -> auto-creates user profile in Firestore at users/{uid} with role "student"
7. Verification that Firestore document ID is the exact Firebase UID
8. PUT /api/users/me -> updates profile fields in Firestore
9. Reading updated profile from Firestore
10. Cleanup of test user in Firebase Auth and Firestore
"""

import os
import sys
import uuid
import httpx
from fastapi.testclient import TestClient

# Ensure app package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db, get_auth_client
from app.main import app

WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")
client = TestClient(app)


def run_e2e_auth_test():
    print("==================================================================")
    print("STARTING REAL FIREBASE AUTH -> FASTAPI -> FIRESTORE END-TO-END TEST")
    print("==================================================================")

    # Generate unique test user
    random_id = uuid.uuid4().hex[:6]
    test_email = f"student_sih_{random_id}@academialink.edu"
    test_password = "SecurePassword123!"

    print(f"\n[Step 1] Registering real user in Firebase Auth: {test_email}...")
    signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={WEB_API_KEY}"
    resp_signup = httpx.post(
        signup_url,
        json={"email": test_email, "password": test_password, "returnSecureToken": True},
        timeout=10.0,
    )
    assert resp_signup.status_code == 200, f"Signup failed: {resp_signup.text}"
    signup_data = resp_signup.json()
    uid = signup_data["localId"]
    id_token = signup_data["idToken"]
    print(f"  [PASS] User created in Firebase Auth with UID: {uid}")

    try:
        print(f"\n[Step 2] Signing in with real user to get fresh ID token...")
        signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"
        resp_signin = httpx.post(
            signin_url,
            json={"email": test_email, "password": test_password, "returnSecureToken": True},
            timeout=10.0,
        )
        assert resp_signin.status_code == 200, f"Signin failed: {resp_signin.text}"
        signin_data = resp_signin.json()
        fresh_token = signin_data["idToken"]
        assert fresh_token, "Received fresh ID token"
        print("  [PASS] Firebase Auth Login successful! Received valid ID Token.")

        print(f"\n[Step 3] Sending ID Token to FastAPI 'GET /api/users/me'...")
        resp_me = client.get("/api/users/me", headers={"Authorization": f"Bearer {fresh_token}"})
        assert resp_me.status_code == 200, f"GET /api/users/me failed: {resp_me.status_code} {resp_me.text}"
        profile = resp_me.json()

        print(f"  [PASS] FastAPI verified token and returned profile:")
        print(f"         - UID: {profile['uid']}")
        print(f"         - Email: {profile['email']}")
        print(f"         - Default Role: {profile['role']}")
        assert profile["uid"] == uid, f"Expected UID {uid}, got {profile['uid']}"
        assert profile["email"] == test_email
        assert profile["role"] == "student", f"Expected default role 'student', got {profile['role']}"

        print(f"\n[Step 4] Checking real Firestore document at 'users/{uid}'...")
        db = get_db()
        doc = db.collection("users").document(uid).get()
        assert doc.exists, f"Firestore document users/{uid} does not exist!"
        doc_data = doc.to_dict()
        assert doc_data["uid"] == uid
        assert doc_data["role"] == "student"
        print(f"  [PASS] Confirmed Firestore document ID is the exact Firebase UID: users/{uid}")

        print(f"\n[Step 5] Calling 'PUT /api/users/me' to update student profile...")
        update_payload = {
            "name": "Ananya Live Student",
            "institution": "National Institute of Technology Karnataka",
            "degree": "B.Tech",
            "branch": "CSE",
            "cgpa": 8.95,
            "headline": "Aspiring Full-Stack Engineer",
        }
        resp_update = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {fresh_token}"},
            json=update_payload,
        )
        assert resp_update.status_code == 200, f"PUT failed: {resp_update.text}"
        updated_profile = resp_update.json()
        assert updated_profile["name"] == "Ananya Live Student"
        assert updated_profile["institution"] == "National Institute of Technology Karnataka"
        assert updated_profile["cgpa"] == 8.95
        print(f"  [PASS] Profile updated successfully in Firestore via PUT /api/users/me.")

        print(f"\n[Step 6] Calling 'GET /api/users/me' to confirm persistence...")
        resp_get_again = client.get("/api/users/me", headers={"Authorization": f"Bearer {fresh_token}"})
        assert resp_get_again.status_code == 200
        persisted = resp_get_again.json()
        assert persisted["name"] == "Ananya Live Student"
        assert persisted["cgpa"] == 8.95
        print(f"  [PASS] Persisted data re-read correctly from Firestore.")

    finally:
        # Cleanup
        print(f"\n[Cleanup] Cleaning up test user {uid}...")
        auth_client = get_auth_client()
        try:
            auth_client.delete_user(uid)
            print("  [PASS] Deleted test user from Firebase Authentication.")
        except Exception as e:
            print(f"  [WARN] Failed to delete user from Auth: {e}")

        try:
            db = get_db()
            db.collection("users").document(uid).delete()
            print("  [PASS] Deleted test document from Firestore.")
        except Exception as e:
            print(f"  [WARN] Failed to delete doc from Firestore: {e}")

    print("\n==================================================================")
    print("SUCCESS: REAL END-TO-END AUTHENTICATION & FIRESTORE FLOW VERIFIED!")
    print("==================================================================")


def test_e2e_auth():
    run_e2e_auth_test()


if __name__ == "__main__":
    run_e2e_auth_test()

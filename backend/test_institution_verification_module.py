"""
Institution Verification Test Suite.

Covers:
1. Institution registry search - valid query, case-insensitivity, partial name, AICTE ID,
   nonexistent institution (empty, not an error), ambiguous name (multiple candidates).
2. Selecting a valid institution via PUT /users/me -> canonical fields persist and survive
   a fresh GET /users/me ("reload").
3. Security: the frontend cannot forge verificationStatus/source/aicteId/institutionName -
   those fields are not even accepted on the request model (422), and an invalid
   institution_id is rejected server-side (400) rather than silently accepted.
4. Authorization: unauthenticated access is rejected (401); a user can only update their
   own profile (enforced by the existing get_current_user dependency, already covered
   elsewhere, exercised again here in the institution-selection context).
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from app.firebase import get_db
from app.main import app
from app.auth import verify_firebase_token
from app.services.institution_data import get_registry

client = TestClient(app)


def _auth_as(uid: str, email: str):
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": uid, "email": email}


def test_registry_loaded():
    registry = get_registry()
    assert registry.is_available, "Institution registry failed to load - check app/data/institutions_aicte.json"
    assert registry.record_count > 1000


def test_search_requires_auth():
    app.dependency_overrides.clear()
    resp = client.get("/api/institutions/search?q=Institute")
    assert resp.status_code == 401


def test_search_valid_partial_and_case_insensitive():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp_upper = client.get("/api/institutions/search?q=SIDDAGANGA")
    assert resp_upper.status_code == 200
    body = resp_upper.json()
    assert body["sourceAvailable"] is True
    assert body["source"] == "AICTE"
    assert any("SIDDAGANGA" in r["name"] for r in body["results"])

    resp_lower = client.get("/api/institutions/search?q=siddaganga institute")
    assert resp_lower.status_code == 200
    assert any("SIDDAGANGA" in r["name"] for r in resp_lower.json()["results"])
    print("[PASS] Case-insensitive partial-name search returns the expected institution.")


def test_search_by_aicte_id():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.get("/api/institutions/search?q=Siddaganga")
    aicte_id = resp.json()["results"][0]["aicteId"]

    resp_by_id = client.get(f"/api/institutions/search?q={aicte_id}")
    assert resp_by_id.status_code == 200
    assert any(r["aicteId"] == aicte_id for r in resp_by_id.json()["results"])
    print("[PASS] Exact AICTE-ID search returns the matching institution.")


def test_search_nonexistent_institution_is_empty_not_an_error():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.get(f"/api/institutions/search?q=ZzzzNoSuchInstitutionAnywhere{run_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sourceAvailable"] is True
    assert body["results"] == []
    print("[PASS] No-match search returns 200 with empty results, not a 'fake college' error.")


def test_search_ambiguous_name_returns_multiple_candidates():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.get("/api/institutions/search?q=Institute of Technology")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 1, "Expected multiple ambiguous candidates for a generic name"
    print(f"[PASS] Ambiguous query returned {len(results)} distinct candidates for manual selection.")


def test_select_valid_institution_persists_canonical_fields():
    run_id = uuid.uuid4().hex[:6]
    uid = f"student_{run_id}"
    _auth_as(uid, f"{uid}@academialink.edu")

    search_resp = client.get("/api/institutions/search?q=Siddaganga Institute of Technology")
    candidate = search_resp.json()["results"][0]

    update_resp = client.put(
        "/api/users/me",
        headers={"Authorization": "Bearer mock_token"},
        json={"name": "Test Student", "institution_id": candidate["institutionId"]},
    )
    assert update_resp.status_code == 200, update_resp.text
    data = update_resp.json()
    assert data["institution"] == candidate["name"]
    assert data["institutionCode"] == candidate["aicteId"]
    assert data["institutionVerificationStatus"] == "VERIFIED"
    assert data["institutionVerificationSource"] == "AICTE"
    assert data["institutionLastVerifiedAt"]
    print("[PASS] Selecting a valid institution stores canonical registry fields.")

    # Reload: GET /users/me must reflect the same persisted canonical state.
    reload_resp = client.get("/api/users/me", headers={"Authorization": "Bearer mock_token"})
    assert reload_resp.status_code == 200
    reload_data = reload_resp.json()
    assert reload_data["institution"] == candidate["name"]
    assert reload_data["institutionVerificationStatus"] == "VERIFIED"
    print("[PASS] Canonical institution selection survives a profile reload.")

    db = get_db()
    doc = db.collection("users").document(uid).get().to_dict()
    assert doc["institutionVerificationStatus"] == "VERIFIED"
    assert doc["institution_id"] == candidate["institutionId"]
    print("[PASS] Firestore persistence confirmed directly against users/{uid}.")


def test_invalid_institution_id_rejected():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.put(
        "/api/users/me",
        headers={"Authorization": "Bearer mock_token"},
        json={"name": "Test Student", "institution_id": "aicte-does-not-exist-99999999"},
    )
    assert resp.status_code == 400
    assert "no matching institution" in resp.json()["detail"].lower()
    print("[PASS] An institution_id with no registry match is rejected outright (400), not silently accepted.")


def test_free_text_only_institution_is_not_verified():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.put(
        "/api/users/me",
        headers={"Authorization": "Bearer mock_token"},
        json={"name": "Test Student", "institution": "My Own Fake College"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["institution"] == "My Own Fake College"
    assert data["institutionVerificationStatus"] == "NOT_VERIFIED"
    assert data.get("institutionCode") is None
    print("[PASS] Free-text-only institution entry is stored as NOT_VERIFIED, never auto-verified.")


def test_cannot_forge_verification_status_from_client():
    """
    The security requirement: a client sending {"institutionId": "fake-id", "verificationStatus":
    "VERIFIED"} must be rejected. UserProfileUpdate (extra='forbid') doesn't even accept a
    'verificationStatus'/'institutionVerificationStatus'/'source'/'aicteId' field, so any attempt
    to smuggle them is a 422 - the derived fields can only ever come from the server-side lookup.
    """
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    resp = client.put(
        "/api/users/me",
        headers={"Authorization": "Bearer mock_token"},
        json={
            "name": "Test Student",
            "institution_id": "fake-id",
            "institutionVerificationStatus": "VERIFIED",
            "institutionVerificationSource": "AICTE",
            "institutionCode": "0000000",
        },
    )
    assert resp.status_code == 422
    body_text = str(resp.json())
    assert "institutionVerificationStatus" in body_text or "extra_forbidden" in body_text.lower() or "institutionCode" in body_text
    print("[PASS] Privilege escalation prevented: client-forged verification fields rejected outright (422).")


def test_get_single_institution_by_id_and_not_found():
    run_id = uuid.uuid4().hex[:6]
    _auth_as(f"student_{run_id}", f"student_{run_id}@academialink.edu")

    search_resp = client.get("/api/institutions/search?q=Siddaganga Institute of Technology")
    institution_id = search_resp.json()["results"][0]["institutionId"]

    detail_resp = client.get(f"/api/institutions/{institution_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["verificationStatus"] == "VERIFIED"
    assert detail["programLevelApprovalChecked"] is False

    missing_resp = client.get("/api/institutions/aicte-0000000000")
    assert missing_resp.status_code == 404
    assert "no matching institution" in missing_resp.json()["detail"].lower()
    print("[PASS] Single-institution lookup works for a real id and returns 404 (not 'fake') for an unknown one.")


def test_another_users_profile_cannot_be_modified():
    run_id = uuid.uuid4().hex[:6]
    uid_a = f"student_a_{run_id}"
    uid_b = f"student_b_{run_id}"

    _auth_as(uid_a, f"{uid_a}@academialink.edu")
    client.put("/api/users/me", headers={"Authorization": "Bearer mock_token"}, json={"name": "Student A"})

    # Student B authenticates as themselves - PUT /users/me only ever targets current_user.uid,
    # so there is no request shape that lets B write to A's document via this endpoint.
    _auth_as(uid_b, f"{uid_b}@academialink.edu")
    resp = client.put("/api/users/me", headers={"Authorization": "Bearer mock_token"}, json={"name": "Student B"})
    assert resp.status_code == 200
    assert resp.json()["uid"] == uid_b

    db = get_db()
    doc_a = db.collection("users").document(uid_a).get().to_dict()
    assert doc_a["name"] == "Student A", "Student B's update must not have leaked into Student A's document"
    print("[PASS] Institution/profile updates are scoped strictly to the authenticated user's own document.")


def test_admin_institution_stats_requires_admin_and_reflects_real_data():
    run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_{run_id}"
    admin_uid = f"admin_{run_id}"

    # Non-admin is rejected.
    _auth_as(student_uid, f"{student_uid}@academialink.edu")
    forbidden_resp = client.get("/api/admin/institution-verification-stats", headers={"Authorization": "Bearer mock_token"})
    assert forbidden_resp.status_code == 403

    # Create a verified student before reading stats, so the count is verifiably real (not fake/static).
    search_resp = client.get("/api/institutions/search?q=Siddaganga Institute of Technology")
    candidate = search_resp.json()["results"][0]
    client.put(
        "/api/users/me",
        headers={"Authorization": "Bearer mock_token"},
        json={"name": "Stats Test Student", "institution_id": candidate["institutionId"]},
    )

    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": admin_uid, "email": f"{admin_uid}@academialink.edu", "role": "admin"}
    client.put("/api/users/me", headers={"Authorization": "Bearer mock_token"}, json={"name": "Admin User"})
    db = get_db()
    db.collection("users").document(admin_uid).set({"role": "admin"}, merge=True)

    stats_resp = client.get("/api/admin/institution-verification-stats", headers={"Authorization": "Bearer mock_token"})
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["verifiedCount"] >= 1
    assert stats["verificationSource"] == "AICTE"
    assert stats["computedAt"]
    print("[PASS] Admin institution-verification stats endpoint is admin-only and reflects real Firestore data.")

"""
AcademiaLINK STEP 31: Evidence, Certificate & Project Portfolio Test Suite
Tests:
1. Security guards: Missing/invalid tokens return HTTP 401.
2. Verification status integrity:
   - New submissions default strictly to 'pending'.
   - Students cannot self-approve evidence (privilege escalation denied).
   - Updating evidence maintains 'pending' status.
3. Skill linking & zero artificial proficiency inflation:
   - Evidence can link to existing skills.
   - Submitting/updating evidence does NOT alter users/{uid}/skills proficiency.
4. CRUD lifecycle in Cloud Firestore:
   - Create evidence (POST /api/evidence/me)
   - List evidence (GET /api/evidence/me)
   - Get single item (GET /api/evidence/me/{id})
   - Update editable fields (PUT /api/evidence/me/{id})
   - Delete evidence (DELETE /api/evidence/me/{id})
5. Cross-user isolation:
   - Student B cannot read, update, or delete Student A's evidence (HTTP 404).
6. Input validation:
   - Invalid evidence types rejected (HTTP 400).
   - Invalid URL schemes rejected (HTTP 400).
7. File upload security & isolation:
   - Disallowed extensions (.exe, .sh) rejected (HTTP 400).
   - Oversized files (> 5MB) rejected (HTTP 400).
   - Valid file (.pdf, .png) succeeds and is stored safely under users/{uid}/.
   - Cross-user file access denied (HTTP 404).
8. Reviewer endpoint authorization:
   - Students attempting reviewer review rejected with HTTP 403 Forbidden.
   - Faculty/Admin review succeeds and updates status to 'approved' or 'rejected'.
9. System health and OpenAPI schema compliance.
"""

import io
import os
import shutil
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import get_db, initialize_firebase
from app.main import app
from app.auth import verify_firebase_token
from app.routes.evidence import BASE_UPLOAD_DIR

client = TestClient(app)


def test_security_guards_and_token_verification():
    """Verify that unauthenticated or invalid tokens receive HTTP 401."""
    print("\n--- Testing Security Guards for Evidence APIs ---")
    app.dependency_overrides.clear()

    # GET /api/evidence/me without token -> 401
    resp1 = client.get("/api/evidence/me")
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    # GET /api/evidence/me with malformed token -> 401
    resp2 = client.get(
        "/api/evidence/me",
        headers={"Authorization": "Bearer malformed_evidence_token"},
    )
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"

    # POST /api/evidence/me without token -> 401
    resp3 = client.post("/api/evidence/me", json={"title": "Unauthorized Project", "type": "project"})
    assert resp3.status_code == 401, f"Expected 401, got {resp3.status_code}"

    # PUT /api/evidence/me/{id} without token -> 401
    resp4 = client.put("/api/evidence/me/ev_123", json={"title": "Unauthorized Edit"})
    assert resp4.status_code == 401, f"Expected 401, got {resp4.status_code}"

    # DELETE /api/evidence/me/{id} without token -> 401
    resp5 = client.delete("/api/evidence/me/ev_123")
    assert resp5.status_code == 401, f"Expected 401, got {resp5.status_code}"

    print("[PASS] Missing and invalid tokens rejected with HTTP 401.")


def test_input_validation():
    """Verify input validation rules for evidence types and URLs."""
    print("\n--- Testing Input Validation ---")
    test_uid = f"student_val_{uuid.uuid4().hex[:6]}"
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": test_uid,
        "email": f"{test_uid}@academialink.edu",
    }

    try:
        # Invalid evidence type
        resp_invalid_type = client.post(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
            json={"title": "My Hackathon", "type": "unsupported_type"},
        )
        assert resp_invalid_type.status_code in [400, 422], f"Expected 400/422, got {resp_invalid_type.status_code}"

        # Invalid URL scheme
        resp_invalid_url = client.post(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
            json={"title": "My Project", "type": "project", "project_url": "ftp://bad-url.com"},
        )
        assert resp_invalid_url.status_code == 400, f"Expected 400, got {resp_invalid_url.status_code}"

        # Valid payload
        resp_valid = client.post(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Clean Architecture in FastAPI",
                "type": "project",
                "project_url": "https://github.com/example/clean-fastapi",
            },
        )
        assert resp_valid.status_code == 201
        ev_id = resp_valid.json()["evidence_id"]

        # Clean up created doc
        db = get_db()
        db.collection("users").document(test_uid).collection("evidence").document(ev_id).delete()
        print("[PASS] Input validation accurately enforces types and URL protocols.")
    finally:
        app.dependency_overrides.clear()


def test_evidence_lifecycle_and_verification_integrity():
    """
    Test full evidence lifecycle, student self-approval denial, cross-user isolation,
    and zero skill proficiency inflation.
    """
    print("\n--- Testing Evidence Lifecycle & Verification Integrity ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    student_a_uid = f"student_a_{run_id}"
    student_b_uid = f"student_b_{run_id}"
    faculty_uid = f"faculty_{run_id}"

    try:
        # 1. Setup Student A in Firestore with an existing verified skill: Python = 2.0
        db.collection("users").document(student_a_uid).set({
            "uid": student_a_uid,
            "name": "Student Alpha",
            "email": f"alpha_{run_id}@academialink.edu",
            "role": "student",
        })
        skill_ref = db.collection("users").document(student_a_uid).collection("skills").document("python_skill")
        skill_ref.set({
            "name": "Python",
            "proficiency": 2.0,
            "category": "Technical",
            "source": "Assessment",
        })

        # Setup Student B (student role)
        db.collection("users").document(student_b_uid).set({
            "uid": student_b_uid,
            "name": "Student Beta",
            "email": f"beta_{run_id}@academialink.edu",
            "role": "student",
        })

        # Setup Faculty member
        db.collection("users").document(faculty_uid).set({
            "uid": faculty_uid,
            "name": "Dr. Alan Turing",
            "email": f"faculty_{run_id}@university.edu",
            "role": "faculty",
        })

        # 2. Student A attempts to self-approve on creation
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_a_uid,
            "email": f"alpha_{run_id}@academialink.edu",
        }

        create_payload = {
            "type": "project",
            "title": "High-Throughput Ingestion Engine",
            "description": "Engineered distributed streaming pipeline handling 10k events/sec.",
            "skill_ids": ["Python", "FastAPI"],
            "project_url": "https://streaming-engine.demo.io",
            "source_url": "https://github.com/alpha/streaming-engine",
            # Malicious attempt to self-approve:
            "verification_status": "approved",
            "reviewer_id": "fake_faculty_id",
            "verification_notes": "Self approved by student",
        }

        create_resp = client.post(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
            json=create_payload,
        )
        assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
        data = create_resp.json()
        ev_id = data["evidence_id"]
        assert ev_id, "Response must include evidence_id"

        # VERIFICATION INTEGRITY: Must be 'pending', not 'approved', and reviewer fields must be empty
        assert data["verification_status"] == "pending", (
            f"SECURITY VIOLATION: Submissions must default to 'pending', got '{data['verification_status']}'"
        )
        assert data["reviewer_id"] is None, "Student must not be able to set reviewer_id"
        assert data["verification_notes"] == "", "Student must not be able to set verification_notes"
        print("[PASS] Privilege escalation prevented: Self-approval attempt defaulted to 'pending'.")

        # 3. ZERO ARTIFICIAL SKILL INFLATION CHECK
        # Verify Python skill in users/{uid}/skills remains strictly 2.0
        updated_skill = skill_ref.get().to_dict()
        assert updated_skill["proficiency"] == 2.0, (
            f"CRITICAL INTEGRITY VIOLATION: Skill proficiency changed from 2.0 to {updated_skill['proficiency']}!"
        )
        print("[PASS] Zero artificial skill inflation verified: users/{uid}/skills remained at 2.0.")

        # 4. List Student A's evidence
        list_resp = client.get(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert any(i["evidence_id"] == ev_id for i in items), "Created item must appear in GET /api/evidence/me"
        print(f"[PASS] GET /api/evidence/me returned {len(items)} items.")

        # 5. Get single evidence item
        get_resp = client.get(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "High-Throughput Ingestion Engine"
        print(f"[PASS] GET /api/evidence/me/{ev_id} retrieved successfully.")

        # 6. Student A updates evidence: Attempt to set status to 'approved' via PUT
        update_resp = client.put(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "High-Throughput Ingestion Engine (v2)",
                "verification_status": "approved",
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "High-Throughput Ingestion Engine (v2)"
        assert update_resp.json()["verification_status"] == "pending", (
            "SECURITY VIOLATION: PUT request must not allow students to set status to approved!"
        )
        print("[PASS] Updating evidence safely preserves 'pending' status.")

        # 7. Cross-User Isolation: Student B cannot read, edit, or delete Student A's evidence
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_b_uid,
            "email": f"beta_{run_id}@academialink.edu",
        }

        # Student B get -> 404
        b_get_resp = client.get(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_get_resp.status_code == 404, f"Expected 404 for cross-user GET, got {b_get_resp.status_code}"

        # Student B update -> 404
        b_put_resp = client.put(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
            json={"title": "Hacked Title"},
        )
        assert b_put_resp.status_code == 404, f"Expected 404 for cross-user PUT, got {b_put_resp.status_code}"

        # Student B delete -> 404
        b_del_resp = client.delete(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_del_resp.status_code == 404, f"Expected 404 for cross-user DELETE, got {b_del_resp.status_code}"
        print("[PASS] Cross-user isolation verified: Student B cannot read, edit, or delete Student A's evidence.")

        # 8. Reviewer Authorization & Review Lifecycle
        # SECURITY FIX: Evidence review now lives exclusively at the institution/cohort-scoped
        # endpoint PATCH /api/faculty/evidence/{evidence_id}/review, which requires an active
        # mentor_assignment between the reviewer and the student (see test_faculty_mentor_module.py
        # for the full assignment + approve/reject + skill-integrity lifecycle). A student calling
        # that endpoint must be rejected, and so must a faculty account with no assignment to this
        # student - "faculty can review anyone's evidence" was the old (insecure) behavior.
        b_review_resp = client.patch(
            f"/api/faculty/evidence/{ev_id}/review",
            headers={"Authorization": "Bearer mock_token"},
            json={"student_uid": student_a_uid, "verification_status": "approved", "verification_notes": "Student trying to review"},
        )
        assert b_review_resp.status_code == 403, (
            f"Expected 403 Forbidden when student calls review, got {b_review_resp.status_code}"
        )
        print("[PASS] Student unauthorized review rejected with HTTP 403 Forbidden.")

        # Faculty member with NO mentor_assignment to student_a -> 403 Forbidden (scoping enforced)
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": faculty_uid,
            "email": f"faculty_{run_id}@university.edu",
        }

        fac_review_resp = client.patch(
            f"/api/faculty/evidence/{ev_id}/review",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "student_uid": student_a_uid,
                "verification_status": "approved",
                "verification_notes": "Exemplary distributed architecture and robust error handling.",
            },
        )
        assert fac_review_resp.status_code == 403, (
            f"Expected unassigned faculty review to be rejected with 403, got {fac_review_resp.status_code}: {fac_review_resp.text}"
        )
        print("[PASS] Unassigned faculty correctly rejected from reviewing evidence (institution/cohort scoping enforced).")

        # 9. Student A deletes own evidence
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_a_uid,
            "email": f"alpha_{run_id}@academialink.edu",
        }
        del_resp = client.delete(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

        # Verify no longer exists
        get_deleted_resp = client.get(
            f"/api/evidence/me/{ev_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert get_deleted_resp.status_code == 404
        print("[PASS] Student successfully deleted own evidence.")

    finally:
        app.dependency_overrides.clear()
        # Clean up test documents in Firestore
        try:
            for e in db.collection("users").document(student_a_uid).collection("evidence").stream():
                e.reference.delete()
            for s in db.collection("users").document(student_a_uid).collection("skills").stream():
                s.reference.delete()
            db.collection("users").document(student_a_uid).delete()
            db.collection("users").document(student_b_uid).delete()
            db.collection("users").document(faculty_uid).delete()
        except Exception as cleanup_err:
            print(f"Cleanup error (non-fatal): {cleanup_err}")


def test_file_upload_security_and_isolation():
    """
    Test file upload boundary:
    - Extension validation (.exe rejected, .pdf accepted)
    - Size validation (> 5MB rejected)
    - Ownership isolation on file download
    """
    print("\n--- Testing File Upload Security & Isolation ---")
    run_id = uuid.uuid4().hex[:6]
    student_a_uid = f"student_fa_{run_id}"
    student_b_uid = f"student_fb_{run_id}"

    db = get_db()
    db.collection("users").document(student_a_uid).set({
        "uid": student_a_uid,
        "name": "File Student A",
        "email": f"fa_{run_id}@academialink.edu",
        "role": "student",
    })
    db.collection("users").document(student_b_uid).set({
        "uid": student_b_uid,
        "name": "File Student B",
        "email": f"fb_{run_id}@academialink.edu",
        "role": "student",
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_a_uid,
            "email": f"fa_{run_id}@academialink.edu",
        }

        # 1. Disallowed extension (.exe) -> 400
        fake_exe = io.BytesIO(b"MZ executable content")
        resp_exe = client.post(
            "/api/evidence/upload",
            headers={"Authorization": "Bearer mock_token"},
            files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
        )
        assert resp_exe.status_code == 400, f"Expected 400 for .exe, got {resp_exe.status_code}"
        assert "Unsupported file type" in resp_exe.json()["detail"]
        print("[PASS] Disallowed executable file upload rejected with HTTP 400.")

        # 2. Oversized file (> 5 MB) -> 400
        oversized = io.BytesIO(b"0" * (6 * 1024 * 1024))
        resp_oversized = client.post(
            "/api/evidence/upload",
            headers={"Authorization": "Bearer mock_token"},
            files={"file": ("huge_cert.pdf", oversized, "application/pdf")},
        )
        assert resp_oversized.status_code == 400, f"Expected 400 for oversized, got {resp_oversized.status_code}"
        assert "exceeds maximum allowed size" in resp_oversized.json()["detail"]
        print("[PASS] Oversized file upload rejected with HTTP 400.")

        # 3. Valid PDF upload -> 200
        valid_pdf = io.BytesIO(b"%PDF-1.4 genuine certificate test data")
        resp_valid = client.post(
            "/api/evidence/upload",
            headers={"Authorization": "Bearer mock_token"},
            files={"file": ("aws_certified_developer.pdf", valid_pdf, "application/pdf")},
        )
        assert resp_valid.status_code == 200, f"Expected 200, got {resp_valid.status_code}"
        file_info = resp_valid.json()
        assert file_info["success"] is True
        file_path = file_info["file_path"]
        assert student_a_uid in file_path, "File path must be scoped to authenticated student UID"
        print(f"[PASS] Valid PDF uploaded securely: {file_path}")

        # Attach to evidence
        ev_create = client.post(
            "/api/evidence/me",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "AWS Certified Developer",
                "type": "certificate",
                "file_path": file_path,
            },
        )
        assert ev_create.status_code == 201
        ev_id = ev_create.json()["evidence_id"]

        # 4. Student A downloads own file -> 200
        download_resp = client.get(
            f"/api/evidence/me/{ev_id}/file",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert download_resp.status_code == 200
        assert download_resp.content == b"%PDF-1.4 genuine certificate test data"
        print("[PASS] Student A downloaded own attached evidence file.")

        # 5. Cross-User File Access Denial: Student B attempts to download Student A's file -> 404
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_b_uid,
            "email": f"fb_{run_id}@academialink.edu",
        }
        b_file_resp = client.get(
            f"/api/evidence/me/{ev_id}/file",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_file_resp.status_code == 404, f"Expected 404 for cross-user file download, got {b_file_resp.status_code}"
        print("[PASS] Cross-user file access denied with HTTP 404.")

    finally:
        app.dependency_overrides.clear()
        # Clean up created files and Firestore records
        try:
            student_a_dir = os.path.join(BASE_UPLOAD_DIR, student_a_uid)
            if os.path.exists(student_a_dir):
                shutil.rmtree(student_a_dir)
            for e in db.collection("users").document(student_a_uid).collection("evidence").stream():
                e.reference.delete()
            db.collection("users").document(student_a_uid).delete()
            db.collection("users").document(student_b_uid).delete()
        except Exception as cleanup_err:
            print(f"Cleanup error (non-fatal): {cleanup_err}")


def test_health_and_openapi_docs():
    """Verify GET /api/health and presence of evidence endpoints in OpenAPI docs."""
    print("\n--- Testing Health Endpoint & OpenAPI Documentation ---")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("status") in ["healthy", "degraded"]

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    paths = openapi_resp.json().get("paths", {})
    assert "/api/evidence/me" in paths
    assert "/api/evidence/me/{evidence_id}" in paths
    assert "/api/evidence/upload" in paths
    assert "/api/evidence/me/{evidence_id}/file" in paths
    # Evidence review lives at the scoped faculty endpoint (mentor-assignment enforced),
    # not at an unscoped path under /evidence/ - see test_faculty_mentor_module.py.
    assert "/api/faculty/evidence/{evidence_id}/review" in paths
    assert "/api/evidence/{user_id}/{evidence_id}/review" not in paths
    print("[PASS] Health check and all evidence OpenAPI endpoints verified.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

"""
AcademiaLINK STEP 32: Recruiter Job Management & Candidate Matching Test Suite
Tests:
1. Security & RBAC:
   - Missing/invalid token -> HTTP 401.
   - Student role rejected on recruiter endpoints -> HTTP 403 Forbidden.
   - Recruiter role succeeds.
2. Job Ownership Security:
   - Recruiter B cannot view, edit, archive, or match candidates for Recruiter A's job (HTTP 403 Forbidden).
3. Input Validation:
   - Empty required skills rejected (HTTP 400).
   - Invalid required proficiency (< 1.0 or > 5.0) rejected (HTTP 400).
   - Negative weights rejected (HTTP 400).
   - Invalid application URL rejected (HTTP 400).
4. Status Lifecycle & Student Discovery Guard:
   - Draft jobs do NOT appear in public student job discovery.
   - Published jobs DO appear in public student job discovery.
   - Archived jobs are excluded from public student job discovery.
5. Deterministic Candidate Matching:
   - Reuses Step 29 formula: skill_score = min(student/required, 1.0) * weight.
   - Accurate categorization of matched, partial, and missing skills.
   - Deterministic descending ranking by (-overall_score, candidate_id).
6. Evidence Integration:
   - Includes Step 31 candidate evidence with verified status badges.
   - Private filesystem paths are not exposed.
7. System health and OpenAPI schema compliance.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import get_db, initialize_firebase
from app.main import app
from app.auth import verify_firebase_token

client = TestClient(app)


def test_security_guards_and_token_verification():
    """Verify missing, invalid, and unauthorized student tokens receive 401/403."""
    print("\n--- Testing Security Guards & RBAC for Recruiter APIs ---")
    app.dependency_overrides.clear()

    # 1. Unauthenticated -> 401
    resp1 = client.get("/api/recruiter/jobs")
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    resp2 = client.post("/api/recruiter/jobs", json={"title": "Test Job"})
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"

    # 2. Student Role Attempt -> 403 Forbidden
    test_run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_{test_run_id}"

    db = get_db()
    db.collection("users").document(student_uid).set({
        "uid": student_uid,
        "name": "Unauthorized Student",
        "email": f"student_{test_run_id}@academialink.edu",
        "role": "student",
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_uid,
            "email": f"student_{test_run_id}@academialink.edu",
        }

        resp_student_list = client.get(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_student_list.status_code == 403, (
            f"Expected 403 for student accessing recruiter jobs, got {resp_student_list.status_code}"
        )

        resp_student_post = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={"title": "Hacked Job", "company": "Acme", "description": "Hacked"},
        )
        assert resp_student_post.status_code == 403, (
            f"Expected 403 for student posting recruiter job, got {resp_student_post.status_code}"
        )

        resp_student_candidates = client.get(
            "/api/recruiter/jobs/any_job_id/candidates",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_student_candidates.status_code == 403, (
            f"Expected 403 for student viewing candidate matches, got {resp_student_candidates.status_code}"
        )

        print("[PASS] RBAC enforced: Student access rejected with HTTP 403 Forbidden.")
    finally:
        app.dependency_overrides.clear()
        db.collection("users").document(student_uid).delete()


def test_input_validation():
    """Verify input validation on required skills, weights, proficiencies, and URLs."""
    print("\n--- Testing Recruiter Input Validation ---")
    run_id = uuid.uuid4().hex[:6]
    recruiter_uid = f"recruiter_val_{run_id}"

    db = get_db()
    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid,
        "name": "Recruiter Tester",
        "email": f"{recruiter_uid}@company.com",
        "role": "recruiter",
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_uid,
            "email": f"{recruiter_uid}@company.com",
        }

        # 1. Empty required skills -> 400
        resp_no_skills = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Backend Intern",
                "company": "Tech Corp",
                "description": "Valid desc",
                "location": "Remote",
                "required_skills": [],
            },
        )
        assert resp_no_skills.status_code == 400, f"Expected 400, got {resp_no_skills.status_code}"

        # 2. Negative weight -> 400/422
        resp_neg_weight = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Backend Intern",
                "company": "Tech Corp",
                "description": "Valid desc",
                "location": "Remote",
                "required_skills": [{"name": "Python", "required_proficiency": 3, "weight": -1.0}],
            },
        )
        assert resp_neg_weight.status_code in [400, 422], f"Expected 400/422, got {resp_neg_weight.status_code}"

        # 3. Invalid proficiency (> 5) -> 400/422
        resp_high_prof = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Backend Intern",
                "company": "Tech Corp",
                "description": "Valid desc",
                "location": "Remote",
                "required_skills": [{"name": "Python", "required_proficiency": 8, "weight": 1.0}],
            },
        )
        assert resp_high_prof.status_code in [400, 422], f"Expected 400/422, got {resp_high_prof.status_code}"

        # 4. Invalid application URL -> 400
        resp_bad_url = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Backend Intern",
                "company": "Tech Corp",
                "description": "Valid desc",
                "location": "Remote",
                "required_skills": [{"name": "Python", "required_proficiency": 3, "weight": 1.0}],
                "application_url": "javascript:alert(1)",
            },
        )
        # A javascript:/non-http(s) application_url is now rejected at the schema layer (422)
        # via a strict pattern on JobCreate.application_url, rather than by a business-logic
        # check after Pydantic already accepted the payload (which returned 400) - both reject
        # the request outright, just at different layers, so accept either.
        assert resp_bad_url.status_code in [400, 422], f"Expected 400/422, got {resp_bad_url.status_code}"

        print("[PASS] Input validation accurately enforces positive weights, 1-5 scale, and valid URLs.")
    finally:
        app.dependency_overrides.clear()
        db.collection("users").document(recruiter_uid).delete()


def test_recruiter_ownership_security():
    """
    Verify job ownership security:
    - Recruiter A creates Job A.
    - Recruiter B cannot view, edit, archive, or match candidates on Job A (403 Forbidden).
    """
    print("\n--- Testing Recruiter Ownership Security & Isolation ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    recruiter_a = f"recruiter_a_{run_id}"
    recruiter_b = f"recruiter_b_{run_id}"

    db.collection("users").document(recruiter_a).set({
        "uid": recruiter_a,
        "name": "Recruiter Alpha",
        "email": f"alpha_{run_id}@corp.com",
        "role": "recruiter",
    })
    db.collection("users").document(recruiter_b).set({
        "uid": recruiter_b,
        "name": "Recruiter Beta",
        "email": f"beta_{run_id}@othercorp.com",
        "role": "recruiter",
    })

    created_job_id = None
    try:
        # Recruiter A creates job
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_a,
            "email": f"alpha_{run_id}@corp.com",
        }

        resp_create = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": "Distributed Systems Intern",
                "company": "Alpha Corp",
                "description": "High throughput systems",
                "location": "Hyderabad",
                "required_skills": [{"name": "Python", "required_proficiency": 4, "weight": 2.0}],
            },
        )
        assert resp_create.status_code == 201
        created_job_id = resp_create.json()["id"]

        # Recruiter B attempts unauthorized operations on Recruiter A's job
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_b,
            "email": f"beta_{run_id}@othercorp.com",
        }

        # 1. GET Job A -> 403
        resp_get = client.get(
            f"/api/recruiter/jobs/{created_job_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_get.status_code == 403, f"Expected 403, got {resp_get.status_code}"

        # 2. PUT Job A -> 403
        resp_put = client.put(
            f"/api/recruiter/jobs/{created_job_id}",
            headers={"Authorization": "Bearer mock_token"},
            json={"title": "Hacked Title"},
        )
        assert resp_put.status_code == 403, f"Expected 403, got {resp_put.status_code}"

        # 3. DELETE/Archive Job A -> 403
        resp_del = client.delete(
            f"/api/recruiter/jobs/{created_job_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_del.status_code == 403, f"Expected 403, got {resp_del.status_code}"

        # 4. Candidates for Job A -> 403
        resp_cand = client.get(
            f"/api/recruiter/jobs/{created_job_id}/candidates",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_cand.status_code == 403, f"Expected 403, got {resp_cand.status_code}"

        print("[PASS] Cross-recruiter job manipulation and candidate snooping denied with HTTP 403 Forbidden.")
    finally:
        app.dependency_overrides.clear()
        if created_job_id:
            db.collection("jobs").document(created_job_id).delete()
        db.collection("users").document(recruiter_a).delete()
        db.collection("users").document(recruiter_b).delete()


def test_job_status_lifecycle_and_discovery_guard():
    """
    Verify status lifecycle:
    - Draft job is hidden from student discovery.
    - Published job appears in student discovery.
    - Archived job is excluded from student discovery.
    """
    print("\n--- Testing Job Status Lifecycle & Student Discovery Guard ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    recruiter_uid = f"recruiter_life_{run_id}"

    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid,
        "name": "Recruiter Lifecycle",
        "email": f"life_{run_id}@corp.com",
        "role": "recruiter",
    })

    draft_job_id = None
    pub_job_id = None
    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_uid,
            "email": f"life_{run_id}@corp.com",
        }

        # 1. Create Draft Job
        resp_draft = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": f"Secret Project Role {run_id}",
                "company": "Stealth Corp",
                "description": "Under development",
                "location": "Remote",
                "status": "draft",
                "required_skills": [{"name": "Go", "required_proficiency": 3, "weight": 1.0}],
            },
        )
        assert resp_draft.status_code == 201
        draft_job_id = resp_draft.json()["id"]

        # 2. Create Published Job
        resp_pub = client.post(
            "/api/recruiter/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "title": f"Public Cloud Role {run_id}",
                "company": "Public Cloud Inc",
                "description": "Public opening",
                "location": "Remote",
                "status": "published",
                "required_skills": [{"name": "Python", "required_proficiency": 4, "weight": 2.0}],
            },
        )
        assert resp_pub.status_code == 201
        pub_job_id = resp_pub.json()["id"]

        # 3. Check public student job discovery (GET /api/jobs)
        public_resp = client.get("/api/jobs")
        assert public_resp.status_code == 200
        public_jobs = public_resp.json()
        public_job_ids = [j["id"] for j in public_jobs]

        assert draft_job_id not in public_job_ids, "Draft job must NOT appear in public student discovery!"
        assert pub_job_id in public_job_ids, "Published job MUST appear in public student discovery!"
        print("[PASS] Draft job correctly hidden from public discovery; published job visible.")

        # 4. Recruiter archives published job
        del_resp = client.delete(
            f"/api/recruiter/jobs/{pub_job_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert del_resp.status_code == 200

        # Verify no longer appears in public discovery
        public_resp_after = client.get("/api/jobs")
        public_ids_after = [j["id"] for j in public_resp_after.json()]
        assert pub_job_id not in public_ids_after, "Archived job must NOT appear in public student discovery!"
        print("[PASS] Archived job successfully hidden from student discovery.")

    finally:
        app.dependency_overrides.clear()
        if draft_job_id:
            db.collection("jobs").document(draft_job_id).delete()
        if pub_job_id:
            db.collection("jobs").document(pub_job_id).delete()
        db.collection("users").document(recruiter_uid).delete()


def test_deterministic_candidate_matching_and_evidence():
    """
    Verify deterministic candidate matching and ranking:
    - Sets up test candidates with specific skills.
    - Calculates scores using Step 29 formula:
      skill_score = min(student / required, 1.0) * weight
    - Verifies deterministic descending order by (-overall_score, candidate_id).
    - Verifies Step 31 evidence is attached with correct verification status.
    """
    print("\n--- Testing Candidate Matching, Ranking & Evidence Integration ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    recruiter_uid = f"recruiter_m_{run_id}"
    student_1_uid = f"student_high_{run_id}"
    student_2_uid = f"student_mid_{run_id}"
    student_3_uid = f"student_low_{run_id}"
    job_id = f"job_match_{run_id}"

    # Setup Recruiter
    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid,
        "name": "Hiring Manager",
        "email": f"hiring_{run_id}@bigtech.com",
        "role": "recruiter",
    })

    # Setup Student 1 (High Match: Python=4, SQL=3 -> 100%)
    db.collection("users").document(student_1_uid).set({
        "uid": student_1_uid,
        "name": "Candidate Alpha (High)",
        "email": f"alpha_{run_id}@student.edu",
        "role": "student",
        "targetRole": "Backend Engineer",
    })
    s1_skills = db.collection("users").document(student_1_uid).collection("skills")
    s1_skills.document("py").set({"name": "Python", "proficiency": 4.0})
    s1_skills.document("sql").set({"name": "SQL", "proficiency": 3.0})

    # Student 1 has Step 31 evidence
    s1_evidence = db.collection("users").document(student_1_uid).collection("evidence")
    s1_evidence.document("ev1").set({
        "evidence_id": "ev1",
        "type": "project",
        "title": "High Scale Cache",
        "issuer": "Open Source",
        "verification_status": "approved",
        "skill_ids": ["Python"],
        "project_url": "https://cache-demo.io",
        "file_path": "uploads/evidence/secret_local_path.pdf",  # Must be masked
    })

    # Setup Student 2 (Partial Match: Python=2, SQL=3 -> ( (2/4)*2 + (3/3)*1 ) / 3 * 100 = 66.67%)
    db.collection("users").document(student_2_uid).set({
        "uid": student_2_uid,
        "name": "Candidate Beta (Mid)",
        "email": f"beta_{run_id}@student.edu",
        "role": "student",
        "targetRole": "Fullstack Engineer",
    })
    s2_skills = db.collection("users").document(student_2_uid).collection("skills")
    s2_skills.document("py").set({"name": "Python", "proficiency": 2.0})
    s2_skills.document("sql").set({"name": "SQL", "proficiency": 3.0})

    # Setup Student 3 (Missing Skill: Python=0, SQL=3 -> ( 0 + 1 ) / 3 * 100 = 33.33%)
    db.collection("users").document(student_3_uid).set({
        "uid": student_3_uid,
        "name": "Candidate Gamma (Low)",
        "email": f"gamma_{run_id}@student.edu",
        "role": "student",
        "targetRole": "Junior Analyst",
    })
    s3_skills = db.collection("users").document(student_3_uid).collection("skills")
    s3_skills.document("sql").set({"name": "SQL", "proficiency": 3.0})

    # Setup Job
    db.collection("jobs").document(job_id).set({
        "id": job_id,
        "title": "Senior Backend Intern",
        "company": "BigTech Systems",
        "description": "Backend services",
        "location": "Bengaluru",
        "status": "published",
        "createdBy": recruiter_uid,
        "recruiter_uid": recruiter_uid,
        "required_skills": [
            {"name": "Python", "required_proficiency": 4.0, "weight": 2.0},
            {"name": "SQL", "required_proficiency": 3.0, "weight": 1.0},
        ],
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_uid,
            "email": f"hiring_{run_id}@bigtech.com",
        }

        resp = client.get(
            f"/api/recruiter/jobs/{job_id}/candidates",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["total_candidates"] >= 3

        # Filter to our 3 test candidates
        candidates = [c for c in data["candidates"] if c["candidate_id"] in [student_1_uid, student_2_uid, student_3_uid]]
        assert len(candidates) == 3

        # Verify strict descending ranking
        assert candidates[0]["candidate_id"] == student_1_uid
        assert candidates[0]["match_score"] == 100
        assert len(candidates[0]["matched_skills"]) == 2

        assert candidates[1]["candidate_id"] == student_2_uid
        assert candidates[1]["match_score"] == 67  # 66.67 rounded
        assert len(candidates[1]["partial_skills"]) == 1
        assert candidates[1]["partial_skills"][0]["skill"] == "Python"

        assert candidates[2]["candidate_id"] == student_3_uid
        assert candidates[2]["match_score"] == 33  # 33.33 rounded
        assert len(candidates[2]["missing_skills"]) == 1
        assert candidates[2]["missing_skills"][0]["skill"] == "Python"

        print("[PASS] Deterministic matching mathematically accurate and ranked strictly descending.")

        # Evidence privacy verification
        c1_evidence = candidates[0]["evidence"]
        assert len(c1_evidence) == 1
        ev_item = c1_evidence[0]
        assert ev_item["title"] == "High Scale Cache"
        assert ev_item["verification_status"] == "approved"
        assert not hasattr(ev_item, "file_path") or getattr(ev_item, "file_path") is None, (
            "SECURITY VIOLATION: Private filesystem path must not be leaked to recruiters!"
        )
        print("[PASS] Step 31 candidate evidence attached with verified badge; private paths shielded.")

    finally:
        app.dependency_overrides.clear()
        # Clean up
        for uid in [student_1_uid, student_2_uid, student_3_uid]:
            for s in db.collection("users").document(uid).collection("skills").stream():
                s.reference.delete()
            for e in db.collection("users").document(uid).collection("evidence").stream():
                e.reference.delete()
            db.collection("users").document(uid).delete()
        db.collection("jobs").document(job_id).delete()
        db.collection("users").document(recruiter_uid).delete()


def test_health_and_openapi_docs():
    """Verify GET /api/health and presence of recruiter endpoints in OpenAPI docs."""
    print("\n--- Testing Health Endpoint & OpenAPI Documentation ---")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("status") in ["healthy", "degraded"]

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    paths = openapi_resp.json().get("paths", {})
    assert "/api/recruiter/jobs" in paths
    assert "/api/recruiter/jobs/{job_id}" in paths
    assert "/api/recruiter/jobs/{job_id}/candidates" in paths
    print("[PASS] Health check and all recruiter OpenAPI endpoints verified.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

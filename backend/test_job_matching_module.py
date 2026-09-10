"""
AcademiaLINK STEP 29: Job Matching & Skill Gap Analysis Test Suite
Tests:
1. Security guards: Missing/invalid tokens return HTTP 401.
2. Recruiter role protection:
   - Authenticated student cannot create jobs (HTTP 403 Forbidden).
   - Recruiter can create jobs in Firestore 'jobs/{job_id}'.
3. Job discovery:
   - Student can list jobs (GET /api/jobs).
   - Student can view individual job (GET /api/jobs/{job_id}).
   - Non-existent job returns HTTP 404.
4. Mathematical accuracy of deterministic weighted matching formula:
   - skill_score = min(student_proficiency / required_proficiency, 1.0)
   - overall_score = (sum(weighted_scores) / sum(weights)) * 100
5. Categorization:
   - matched (gap == 0)
   - partial (0 < student < required)
   - missing (student == 0)
6. Learning priority ordering:
   - Gaps ordered by (-gap_amount, -weight).
7. Live Firestore matching endpoint (GET /api/matching/job/{job_id}).
8. Role spoofing prevention (Firestore role authoritative).
9. Health endpoint and OpenAPI schema validation.
"""

import os
import sys
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import get_db, initialize_firebase
from app.main import app
from app.auth import verify_firebase_token
from app.routes.matching import compute_weighted_job_match

client = TestClient(app)


def test_security_guards_and_token_verification():
    """Verify that unauthenticated or invalid tokens receive HTTP 401."""
    print("\n--- Testing Security Guards for Jobs & Matching APIs ---")

    # Clear any leftover overrides
    app.dependency_overrides.clear()

    # POST /api/jobs without token -> 401
    resp1 = client.post("/api/jobs", json={"title": "Unauthorized Job", "company": "Acme", "description": "test", "location": "Remote"})
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    # POST /api/jobs with malformed token -> 401
    resp2 = client.post(
        "/api/jobs",
        headers={"Authorization": "Bearer invalid_signature_token"},
        json={"title": "Unauthorized Job", "company": "Acme", "description": "test", "location": "Remote"},
    )
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"

    # GET /api/matching/job/{id} without token -> 401
    resp3 = client.get("/api/matching/job/test_job_123")
    assert resp3.status_code == 401, f"Expected 401, got {resp3.status_code}"

    # GET /api/matching/job/{id} with invalid token -> 401
    resp4 = client.get(
        "/api/matching/job/test_job_123",
        headers={"Authorization": "Bearer bad_token"},
    )
    assert resp4.status_code == 401, f"Expected 401, got {resp4.status_code}"

    print("[PASS] Missing and invalid tokens rejected with HTTP 401.")


def test_recruiter_authorization_and_job_creation():
    """
    Verify role-based authorization:
    - Student calling POST /api/jobs is rejected with HTTP 403 Forbidden.
    - Recruiter calling POST /api/jobs succeeds and creates job in Firestore.
    """
    print("\n--- Testing Role Enforcement on Job Creation ---")
    db = get_db()
    test_run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_user_{test_run_id}"
    recruiter_uid = f"recruiter_user_{test_run_id}"

    # Setup student in Firestore with role "student"
    db.collection("users").document(student_uid).set({
        "uid": student_uid,
        "name": "Test Student",
        "email": f"student_{test_run_id}@academialink.edu",
        "role": "student",
    })

    # Setup recruiter in Firestore with role "recruiter"
    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid,
        "name": "Test Recruiter",
        "email": f"recruiter_{test_run_id}@company.com",
        "role": "recruiter",
    })

    job_payload = {
        "title": "Cloud Systems & Backend Engineer Intern",
        "company": "CloudScale Technologies",
        "description": "Design resilient microservices, deploy containers, and optimize queries.",
        "location": "Bengaluru, India (Hybrid)",
        "employment_type": "Internship",
        "workMode": "Hybrid",
        "stipend": "₹45,000/mo",
        "required_skills": [
            {"name": "Python", "required_proficiency": 4.0, "weight": 2.0},
            {"name": "SQL", "required_proficiency": 4.0, "weight": 2.0},
            {"name": "Docker", "required_proficiency": 3.0, "weight": 1.0},
        ],
        "preferred_skills": ["Kubernetes", "FastAPI"],
        "minimum_proficiency": 3,
        "source": "recruiter",
    }

    try:
        # 1. Attempt job creation as student -> must be rejected with 403 Forbidden
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_uid,
            "email": f"student_{test_run_id}@academialink.edu",
        }

        student_resp = client.post(
            "/api/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json=job_payload,
        )
        assert student_resp.status_code == 403, (
            f"Expected student job creation to be rejected with 403, got {student_resp.status_code}: {student_resp.text}"
        )
        print("[PASS] Student rejected with HTTP 403 Forbidden on recruiter job creation.")

        # 2. Attempt job creation as recruiter -> must succeed with 201 Created
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_uid,
            "email": f"recruiter_{test_run_id}@company.com",
        }

        recruiter_resp = client.post(
            "/api/jobs",
            headers={"Authorization": "Bearer mock_token"},
            json=job_payload,
        )
        assert recruiter_resp.status_code == 201, (
            f"Expected recruiter job creation to succeed with 201, got {recruiter_resp.status_code}: {recruiter_resp.text}"
        )
        job_data = recruiter_resp.json()
        job_id = job_data.get("id") or job_data.get("job_id")
        assert job_id, "Response must contain created job ID"
        assert job_data["company"] == "CloudScale Technologies"
        assert job_data["createdBy"] == recruiter_uid
        assert len(job_data["required_skills"]) == 3
        print(f"[PASS] Recruiter created job successfully in Firestore (Job ID: {job_id}).")

        # Verify persisted document directly in Firestore
        doc_snap = db.collection("jobs").document(job_id).get()
        assert doc_snap.exists, f"Job document jobs/{job_id} must exist in Firestore"
        assert doc_snap.to_dict().get("createdBy") == recruiter_uid
        print("[PASS] Firestore jobs collection document verified.")

    finally:
        app.dependency_overrides.clear()


def test_job_discovery_endpoints():
    """Verify GET /api/jobs and GET /api/jobs/{job_id}."""
    print("\n--- Testing Job Discovery Endpoints ---")
    # 1. List jobs
    resp = client.get("/api/jobs")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    jobs = resp.json()
    assert isinstance(jobs, list), "Expected list of jobs"
    print(f"[PASS] GET /api/jobs returned {len(jobs)} jobs.")

    if jobs:
        target_job = jobs[0]
        job_id = target_job["id"]
        # 2. Retrieve single job
        single_resp = client.get(f"/api/jobs/{job_id}")
        assert single_resp.status_code == 200
        single_data = single_resp.json()
        assert single_data["id"] == job_id
        assert "title" in single_data
        assert "company" in single_data
        print(f"[PASS] GET /api/jobs/{job_id} returned expected job details.")

    # 3. Non-existent job
    not_found_resp = client.get("/api/jobs/non_existent_job_id_xyz")
    assert not_found_resp.status_code == 404, f"Expected 404, got {not_found_resp.status_code}"
    print("[PASS] GET /api/jobs/non_existent_id correctly returned HTTP 404.")


def test_mathematical_accuracy_of_weighted_matching():
    """
    Verify mathematical accuracy of weighted matching algorithm:
    Known test vector:
      Required Skills:
        - Python: required_proficiency = 4.0, weight = 2.0
        - SQL:    required_proficiency = 4.0, weight = 2.0
        - Docker: required_proficiency = 3.0, weight = 1.0
      Student Skills:
        - Python: proficiency = 4.0 -> min(4/4, 1.0) = 1.0 -> weighted = 2.0
        - SQL:    proficiency = 2.0 -> min(2/4, 1.0) = 0.5 -> weighted = 1.0
        - Docker: proficiency = 0.0 -> min(0/3, 1.0) = 0.0 -> weighted = 0.0
      Totals:
        - total_weight = 2.0 + 2.0 + 1.0 = 5.0
        - total_weighted_score = 2.0 + 1.0 + 0.0 = 3.0
        - overall_score = (3.0 / 5.0) * 100 = 60.0%
    """
    print("\n--- Testing Mathematical Precision of Matching Algorithm ---")
    required = [
        {"name": "Python", "required_proficiency": 4.0, "weight": 2.0},
        {"name": "SQL", "required_proficiency": 4.0, "weight": 2.0},
        {"name": "Docker", "required_proficiency": 3.0, "weight": 1.0},
    ]
    student = {
        "Python": 4.0,
        "SQL": 2.0,
        # Docker missing
    }

    score, matched, partial, missing, prioritized_gaps, explanation = compute_weighted_job_match(
        student, required
    )

    # 1. Verify score is mathematically exact (60.0%)
    assert score == 60.0, f"Expected 60.0%, got {score}%"
    print("[PASS] Weighted match score calculation is mathematically exact (60.0%).")

    # 2. Verify categorization
    assert len(matched) == 1, f"Expected 1 matched skill, got {len(matched)}"
    assert matched[0].skill == "Python"
    assert matched[0].gap_category == "matched"
    assert matched[0].gap_amount == 0.0
    assert matched[0].skill_score == 1.0
    assert matched[0].weighted_score == 2.0

    assert len(partial) == 1, f"Expected 1 partial skill, got {len(partial)}"
    assert partial[0].skill == "SQL"
    assert partial[0].gap_category == "partial"
    assert partial[0].gap_amount == 2.0
    assert partial[0].skill_score == 0.5
    assert partial[0].weighted_score == 1.0

    assert len(missing) == 1, f"Expected 1 missing skill, got {len(missing)}"
    assert missing[0].skill == "Docker"
    assert missing[0].gap_category == "missing"
    assert missing[0].gap_amount == 3.0
    assert missing[0].skill_score == 0.0
    assert missing[0].weighted_score == 0.0

    print("[PASS] Categories correctly identified: Python=matched, SQL=partial, Docker=missing.")

    # 3. Verify learning priority ordering (-gap_amount, -weight)
    # Docker has gap=3.0, weight=1.0
    # SQL has gap=2.0, weight=2.0
    # Docker gap (3.0) > SQL gap (2.0), so Docker must be first in prioritized gaps
    assert len(prioritized_gaps) == 2
    assert prioritized_gaps[0].skill == "Docker", f"Expected Docker to be highest priority gap, got {prioritized_gaps[0].skill}"
    assert prioritized_gaps[1].skill == "SQL"
    print("[PASS] Learning priorities correctly ordered by largest gap descending.")

    # 4. Verify explanation text is transparent and human-readable
    assert "60.0%" in explanation
    assert "Docker" in explanation
    print(f"[PASS] Explainable result generated: '{explanation}'")


def test_live_matching_endpoint():
    """
    Test GET /api/matching/job/{job_id} end-to-end against live Firestore:
    1. Create a job in Firestore with known weights & proficiencies.
    2. Populate student skills in Firestore subcollection users/{uid}/skills.
    3. Call GET /api/matching/job/{job_id}.
    4. Assert match score, matched skills, partial skills, missing skills, and prioritized gaps.
    """
    print("\n--- Testing Live Matching Endpoint with Firestore Skills ---")
    db = get_db()
    test_run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_match_{test_run_id}"

    # 1. Create student profile in Firestore
    db.collection("users").document(student_uid).set({
        "uid": student_uid,
        "name": "Matching Test Student",
        "email": f"match_{test_run_id}@academialink.edu",
        "role": "student",
    })

    # 2. Add skills to users/{uid}/skills
    # Python = 4, SQL = 2
    db.collection("users").document(student_uid).collection("skills").document("skill_python").set({
        "skillId": "skill_python",
        "name": "Python",
        "proficiency": 4,
        "score": 80,
        "category": "Technical",
    })
    db.collection("users").document(student_uid).collection("skills").document("skill_sql").set({
        "skillId": "skill_sql",
        "name": "SQL",
        "proficiency": 2,
        "score": 40,
        "category": "Technical",
    })

    # 3. Create job in Firestore
    job_ref = db.collection("jobs").document(f"test_job_{test_run_id}")
    job_ref.set({
        "id": job_ref.id,
        "job_id": job_ref.id,
        "title": "Backend Engineering Intern",
        "company": "DataStream Analytics",
        "description": "High performance data pipelines and query optimization.",
        "location": "Remote",
        "employment_type": "Internship",
        "required_skills": [
            {"name": "Python", "required_proficiency": 4.0, "weight": 2.0},
            {"name": "SQL", "required_proficiency": 4.0, "weight": 2.0},
            {"name": "Docker", "required_proficiency": 3.0, "weight": 1.0},
        ],
        "createdBy": "recruiter_admin",
        "createdAt": "2026-09-10T00:00:00Z",
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_uid,
            "email": f"match_{test_run_id}@academialink.edu",
        }

        resp = client.get(
            f"/api/matching/job/{job_ref.id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        assert data["job_id"] == job_ref.id
        assert data["company"] == "DataStream Analytics"
        assert data["overall_score"] == 60.0
        assert data["match_score"] == 60

        # Check matched skills
        matched_skills = data["matched_skills"]
        assert len(matched_skills) == 1
        assert matched_skills[0]["skill"] == "Python"
        assert matched_skills[0]["current_proficiency"] == 4.0

        # Check partial skills
        partial_skills = data["partial_skills"]
        assert len(partial_skills) == 1
        assert partial_skills[0]["skill"] == "SQL"
        assert partial_skills[0]["current_proficiency"] == 2.0
        assert partial_skills[0]["gap_amount"] == 2.0

        # Check missing skills
        missing_skills = data["missing_skills"]
        assert len(missing_skills) == 1
        assert missing_skills[0]["skill"] == "Docker"
        assert missing_skills[0]["current_proficiency"] == 0.0
        assert missing_skills[0]["gap_amount"] == 3.0

        # Check prioritized gaps
        prioritized = data["prioritized_gaps"]
        assert len(prioritized) == 2
        assert prioritized[0]["skill"] == "Docker"
        assert prioritized[1]["skill"] == "SQL"

        assert "60.0%" in data["explanation"]
        print(f"[PASS] Live matching endpoint calculated exact 60.0% match against real Firestore subcollection.")

    finally:
        app.dependency_overrides.clear()
        # Cleanup test records
        try:
            db.collection("users").document(student_uid).collection("skills").document("skill_python").delete()
            db.collection("users").document(student_uid).collection("skills").document("skill_sql").delete()
            db.collection("users").document(student_uid).delete()
            job_ref.delete()
        except Exception:
            pass


def test_health_and_openapi_docs():
    """Verify /api/health and /openapi.json documentation."""
    print("\n--- Testing Health & OpenAPI Documentation ---")
    # Health check
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("firebase_ready") is True
    print("[PASS] GET /api/health returned HTTP 200 with firebase_ready=True.")

    # OpenAPI spec
    docs_resp = client.get("/openapi.json")
    assert docs_resp.status_code == 200
    spec = docs_resp.json()
    paths = spec.get("paths", {})

    assert "/api/jobs" in paths, "OpenAPI spec must document /api/jobs"
    assert "/api/jobs/{job_id}" in paths, "OpenAPI spec must document /api/jobs/{job_id}"
    assert "/api/matching/job/{job_id}" in paths, "OpenAPI spec must document /api/matching/job/{job_id}"
    print("[PASS] OpenAPI documents all job and matching endpoints.")


if __name__ == "__main__":
    initialize_firebase()
    test_security_guards_and_token_verification()
    test_recruiter_authorization_and_job_creation()
    test_job_discovery_endpoints()
    test_mathematical_accuracy_of_weighted_matching()
    test_live_matching_endpoint()
    test_health_and_openapi_docs()
    print("\n================================================================")
    print("ALL STEP 29 JOB MATCHING & SKILL GAP TESTS PASSED!")
    print("================================================================")

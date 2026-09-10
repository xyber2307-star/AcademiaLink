"""
AcademiaLINK STEP 30: Learning Path & Recommendations Test Suite
Tests:
1. Security guards: Missing/invalid tokens return HTTP 401.
2. Mathematical accuracy of deterministic priority calculation:
   - gap = max(required - current, 0)
   - missing_multiplier = 1.25 if is_missing else 1.0
   - priority_score = round(gap * weight * missing_multiplier, 2)
   - High (>= 4.0), Medium (2.0 <= score < 4.0), Low (< 2.0)
3. End-to-end generation of personalized learning path (POST /api/learning-paths):
   - Integrates student's real skills from users/{uid}/skills
   - Target job requirements from jobs/{job_id}
   - Deterministic prioritization and gap ordering
4. Retrieval endpoints:
   - List student's paths (GET /api/learning-paths/me)
   - Retrieve single path (GET /api/learning-paths/me/{path_id})
   - Non-existent path returns HTTP 404
5. Cross-user isolation and ownership:
   - Student B cannot view or modify Student A's learning paths (HTTP 404)
6. Data integrity & progress isolation:
   - Updating syllabus progress to 'completed' tracks within learning path ONLY
   - users/{uid}/skills official verified proficiency remains strictly UNTOUCHED
7. Overall path status lifecycle (active -> completed)
8. System health and OpenAPI schema compliance.
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
from app.routes.learning_paths import calculate_learning_priority

client = TestClient(app)


def test_security_guards_and_token_verification():
    """Verify that unauthenticated or invalid tokens receive HTTP 401."""
    print("\n--- Testing Security Guards for Learning Path APIs ---")
    app.dependency_overrides.clear()

    # GET /api/learning-paths/me without token -> 401
    resp1 = client.get("/api/learning-paths/me")
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    # GET /api/learning-paths/me with malformed token -> 401
    resp2 = client.get(
        "/api/learning-paths/me",
        headers={"Authorization": "Bearer malformed_bad_token"},
    )
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"

    # POST /api/learning-paths without token -> 401
    resp3 = client.post("/api/learning-paths", json={"job_id": "test_job"})
    assert resp3.status_code == 401, f"Expected 401, got {resp3.status_code}"

    # PATCH /api/learning-paths/me/{id}/skills/{skill} without token -> 401
    resp4 = client.patch(
        "/api/learning-paths/me/path_123/skills/skill_python",
        json={"status": "completed"},
    )
    assert resp4.status_code == 401, f"Expected 401, got {resp4.status_code}"

    print("[PASS] Missing and invalid tokens rejected with HTTP 401.")


def test_mathematical_accuracy_of_priority_formula():
    """
    Verify mathematical accuracy and classification of calculate_learning_priority:
    - High: score >= 4.0
    - Medium: 2.0 <= score < 4.0
    - Low: score < 2.0
    """
    print("\n--- Testing Priority Formula Calculations ---")

    # Case 1: High Priority (e.g. Python partial gap=2.0, weight=2.0 -> score=4.0)
    score, prio, reason = calculate_learning_priority(gap=2.0, weight=2.0, is_missing=False)
    assert score == 4.00, f"Expected 4.00, got {score}"
    assert prio == "High"
    assert "Advancing this skill increases candidate competitiveness" in reason

    # Case 2: High Priority with Missing Multiplier (gap=3.0, weight=1.5, missing=True -> 3.0*1.5*1.25 = 5.62)
    score, prio, reason = calculate_learning_priority(gap=3.0, weight=1.5, is_missing=True)
    assert score == 5.62, f"Expected 5.62, got {score}"
    assert prio == "High"
    assert "Missing skill" in reason

    # Case 3: Medium Priority (Docker missing gap=3.0, weight=1.0 -> 3.0*1.0*1.25 = 3.75)
    score, prio, reason = calculate_learning_priority(gap=3.0, weight=1.0, is_missing=True)
    assert score == 3.75, f"Expected 3.75, got {score}"
    assert prio == "Medium"

    # Case 4: Medium Priority Partial (gap=1.0, weight=2.5, partial -> 1.0*2.5*1.0 = 2.50)
    score, prio, reason = calculate_learning_priority(gap=1.0, weight=2.5, is_missing=False)
    assert score == 2.50, f"Expected 2.50, got {score}"
    assert prio == "Medium"

    # Case 5: Low Priority (SQL partial gap=1.0, weight=1.5 -> 1.0*1.5*1.0 = 1.50)
    score, prio, reason = calculate_learning_priority(gap=1.0, weight=1.5, is_missing=False)
    assert score == 1.50, f"Expected 1.50, got {score}"
    assert prio == "Low"

    # Case 6: Edge low gap (gap=0.5, weight=1.0 -> 0.50)
    score, prio, reason = calculate_learning_priority(gap=0.5, weight=1.0, is_missing=False)
    assert score == 0.50, f"Expected 0.50, got {score}"
    assert prio == "Low"

    print("[PASS] Priority calculation matches mathematical specification precisely.")


def test_learning_path_lifecycle_and_progress_isolation():
    """
    Comprehensive end-to-end test:
    1. Create student with initial skills in Firestore.
    2. Create target job in Firestore.
    3. Generate personalized learning path via POST /api/learning-paths.
    4. Verify prioritization order and contents.
    5. Test GET /api/learning-paths/me and GET /api/learning-paths/me/{id}.
    6. Verify cross-user isolation with a second student.
    7. Update skill progress to 'completed' and verify users/{uid}/skills is NOT modified.
    8. Update path status to 'completed'.
    9. Clean up test documents.
    """
    print("\n--- Testing Learning Path Lifecycle & Data Integrity ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    student_a_uid = f"student_a_{run_id}"
    student_b_uid = f"student_b_{run_id}"
    job_id = f"job_dev_{run_id}"

    try:
        # 1. Setup Student A profile and skills
        db.collection("users").document(student_a_uid).set({
            "uid": student_a_uid,
            "name": "Student Alpha",
            "email": f"alpha_{run_id}@academialink.edu",
            "role": "student",
        })

        # Student A skills: Python (2.0), SQL (3.0)
        skills_a_ref = db.collection("users").document(student_a_uid).collection("skills")
        skills_a_ref.document("py_skill").set({
            "name": "Python",
            "proficiency": 2.0,
            "category": "Technical",
            "source": "Assessment",
        })
        skills_a_ref.document("sql_skill").set({
            "name": "SQL",
            "proficiency": 3.0,
            "category": "Technical",
            "source": "Coursework",
        })

        # Setup Student B profile (no skills)
        db.collection("users").document(student_b_uid).set({
            "uid": student_b_uid,
            "name": "Student Beta",
            "email": f"beta_{run_id}@academialink.edu",
            "role": "student",
        })

        # 2. Setup Target Job in Firestore
        db.collection("jobs").document(job_id).set({
            "id": job_id,
            "title": "Full Stack Platform Intern",
            "company": "NextGen Systems",
            "description": "Develop high-scale cloud platforms.",
            "location": "Hyderabad, India (Hybrid)",
            "employment_type": "Internship",
            "required_skills": [
                {"name": "Python", "required_proficiency": 4.0, "weight": 2.0},  # partial gap 2.0, score 4.00 (High)
                {"name": "Docker", "required_proficiency": 3.0, "weight": 1.0},  # missing gap 3.0, score 3.75 (Medium)
                {"name": "React", "required_proficiency": 2.0, "weight": 1.0},   # missing gap 2.0, score 2.50 (Medium)
                {"name": "SQL", "required_proficiency": 4.0, "weight": 1.5},     # partial gap 1.0, score 1.50 (Low)
            ],
            "createdBy": "admin",
        })

        # 3. Generate Learning Path for Student A
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_a_uid,
            "email": f"alpha_{run_id}@academialink.edu",
        }

        post_resp = client.post(
            "/api/learning-paths",
            headers={"Authorization": "Bearer mock_token"},
            json={"job_id": job_id},
        )
        assert post_resp.status_code == 201, (
            f"Expected 201 Created, got {post_resp.status_code}: {post_resp.text}"
        )
        path_data = post_resp.json()
        path_id = path_data["path_id"]
        assert path_id, "Response must include path_id"
        assert path_data["user_id"] == student_a_uid
        assert path_data["target_job_id"] == job_id
        assert path_data["target_job_title"] == "Full Stack Platform Intern"
        assert path_data["target_company"] == "NextGen Systems"
        assert path_data["overall_match_after"] == 100.0
        assert path_data["status"] == "active"

        skills = path_data["skills"]
        assert len(skills) == 4, f"Expected 4 prioritized skills, got {len(skills)}"

        # Verify sorted ordering: Python (4.00) -> Docker (3.75) -> React (2.50) -> SQL (1.50)
        skill_names = [s["skill_name"] for s in skills]
        assert skill_names == ["Python", "Docker", "React", "SQL"], (
            f"Expected prioritized order ['Python', 'Docker', 'React', 'SQL'], got {skill_names}"
        )

        python_item = skills[0]
        assert python_item["priority"] == "High"
        assert python_item["priority_score"] == 4.00
        assert python_item["gap"] == 2.0
        assert python_item["status"] == "not_started"

        docker_item = skills[1]
        assert docker_item["priority"] == "Medium"
        assert docker_item["priority_score"] == 3.75
        assert docker_item["gap"] == 3.0

        sql_item = skills[3]
        assert sql_item["priority"] == "Low"
        assert sql_item["priority_score"] == 1.50
        assert sql_item["gap"] == 1.0

        print(f"[PASS] Successfully generated learning path {path_id} with verified deterministic ranking.")

        # 4. List Student A's Learning Paths
        list_resp = client.get(
            "/api/learning-paths/me",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert list_resp.status_code == 200
        paths_list = list_resp.json()
        assert any(p["path_id"] == path_id for p in paths_list), "Path must be in list"
        print("[PASS] GET /api/learning-paths/me retrieved created learning path.")

        # 5. Retrieve Specific Path
        get_resp = client.get(
            f"/api/learning-paths/me/{path_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["path_id"] == path_id
        print(f"[PASS] GET /api/learning-paths/me/{path_id} returned expected details.")

        # 6. Cross-User Isolation (Student B cannot see or touch Student A's path)
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_b_uid,
            "email": f"beta_{run_id}@academialink.edu",
        }

        # Student B list -> should NOT contain Student A's path
        b_list_resp = client.get(
            "/api/learning-paths/me",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_list_resp.status_code == 200
        assert all(p["path_id"] != path_id for p in b_list_resp.json())

        # Student B direct GET -> 404 Not Found
        b_get_resp = client.get(
            f"/api/learning-paths/me/{path_id}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_get_resp.status_code == 404, f"Expected 404, got {b_get_resp.status_code}"

        # Student B patch -> 404 Not Found
        b_patch_resp = client.patch(
            f"/api/learning-paths/me/{path_id}/skills/skill_docker",
            headers={"Authorization": "Bearer mock_token"},
            json={"status": "completed"},
        )
        assert b_patch_resp.status_code == 404, f"Expected 404, got {b_patch_resp.status_code}"
        print("[PASS] Cross-user isolation verified: Student B cannot read or modify Student A's path.")

        # 7. Update Skill Status & Verify Progress Isolation
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_a_uid,
            "email": f"alpha_{run_id}@academialink.edu",
        }

        patch_skill_resp = client.patch(
            f"/api/learning-paths/me/{path_id}/skills/skill_docker",
            headers={"Authorization": "Bearer mock_token"},
            json={"status": "completed"},
        )
        assert patch_skill_resp.status_code == 200
        updated_skills = patch_skill_resp.json()["skills"]
        docker_updated = next(s for s in updated_skills if s["skill_id"] == "skill_docker")
        assert docker_updated["status"] == "completed"

        # DATA INTEGRITY CHECK: Verify official skills in users/{uid}/skills were NOT inflated
        student_a_skills_snap = list(
            db.collection("users").document(student_a_uid).collection("skills").stream()
        )
        verified_skills_dict = {s.to_dict()["name"]: s.to_dict()["proficiency"] for s in student_a_skills_snap}
        
        assert "Docker" not in verified_skills_dict, (
            "CRITICAL INTEGRITY VIOLATION: Marking Docker completed in learning path must NOT add it to official skills!"
        )
        assert verified_skills_dict["Python"] == 2.0, (
            "CRITICAL INTEGRITY VIOLATION: Official Python skill proficiency was modified!"
        )
        print("[PASS] Data integrity verified: Study progress updated without artificially altering official skills.")

        # 8. Update Learning Path Status
        patch_status_resp = client.patch(
            f"/api/learning-paths/me/{path_id}/status",
            headers={"Authorization": "Bearer mock_token"},
            json={"status": "completed"},
        )
        assert patch_status_resp.status_code == 200
        assert patch_status_resp.json()["status"] == "completed"
        print("[PASS] Overall learning path status updated to completed.")

    finally:
        app.dependency_overrides.clear()
        # Clean up Firestore documents
        try:
            # Delete Student A skills and learning paths
            for s in db.collection("users").document(student_a_uid).collection("skills").stream():
                s.reference.delete()
            for p in db.collection("users").document(student_a_uid).collection("learning_paths").stream():
                p.reference.delete()
            db.collection("users").document(student_a_uid).delete()
            db.collection("users").document(student_b_uid).delete()
            db.collection("jobs").document(job_id).delete()
        except Exception as cleanup_err:
            print(f"Cleanup error (non-fatal): {cleanup_err}")


def test_health_and_openapi_docs():
    """Verify GET /api/health and presence of learning paths endpoints in OpenAPI docs."""
    print("\n--- Testing Health Endpoint & OpenAPI Documentation ---")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("status") in ["healthy", "degraded"]

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    paths = openapi_resp.json().get("paths", {})
    assert "/api/learning-paths/me" in paths
    assert "/api/learning-paths/me/{path_id}" in paths
    assert "/api/learning-paths" in paths
    assert "/api/learning-paths/me/{path_id}/skills/{skill_id}" in paths
    assert "/api/learning-paths/me/{path_id}/status" in paths
    print("[PASS] Health check and all learning paths OpenAPI endpoints verified.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

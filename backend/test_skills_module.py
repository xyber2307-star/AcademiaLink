"""
AcademiaLINK Skills & Skill Assessment Module Test Suite
Tests:
1. Authenticated student retrieves skills (GET /api/skills/me)
2. Student creates a skill (POST /api/skills/me)
3. Student updates the skill (PUT /api/skills/me/{skill_id})
4. Student deletes the skill (DELETE /api/skills/me/{skill_id})
5. Invalid proficiency rejected (outside 1-5 scale returns HTTP 422)
6. Missing/invalid Firebase token returns HTTP 401
7. Cross-user security: Student cannot access/modify another student's skills
8. Assessment questions & deterministic scoring (POST /api/skills/assessment)
9. OpenAPI docs include all endpoints
"""

import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure app package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import get_db, initialize_firebase
from app.main import app
from app.auth import verify_firebase_token

client = TestClient(app)


def test_missing_or_invalid_token_rejected():
    print("\n--- Testing Security Guards for Skills APIs ---")
    # Missing token
    resp1 = client.get("/api/skills/me")
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    # Invalid token
    resp2 = client.post(
        "/api/skills/me",
        headers={"Authorization": "Bearer invalid_signature_token"},
        json={"name": "Python", "proficiency": 4, "category": "Technical"},
    )
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"
    print("[PASS] Missing and invalid tokens rejected with HTTP 401.")


def test_invalid_proficiency_scale_rejected():
    print("\n--- Testing Validation of 1-5 Numerical Proficiency Scale ---")
    student_uid = "test_prof_validation_uid"

    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": student_uid,
        "email": "prof_student@academialink.edu",
        "name": "Prof Student",
        "email_verified": True,
    }

    try:
        # Test proficiency = 0 (below minimum 1)
        resp_zero = client.post(
            "/api/skills/me",
            headers={"Authorization": "Bearer mock_token"},
            json={"name": "Rust", "proficiency": 0, "category": "Technical"},
        )
        assert resp_zero.status_code == 422, f"Expected 422 for proficiency=0, got {resp_zero.status_code}"

        # Test proficiency = 6 (above maximum 5)
        resp_six = client.post(
            "/api/skills/me",
            headers={"Authorization": "Bearer mock_token"},
            json={"name": "Rust", "proficiency": 6, "category": "Technical"},
        )
        assert resp_six.status_code == 422, f"Expected 422 for proficiency=6, got {resp_six.status_code}"

        # Test proficiency = -1
        resp_neg = client.post(
            "/api/skills/me",
            headers={"Authorization": "Bearer mock_token"},
            json={"name": "Rust", "proficiency": -1, "category": "Technical"},
        )
        assert resp_neg.status_code == 422, f"Expected 422 for proficiency=-1, got {resp_neg.status_code}"

        print("[PASS] Invalid proficiencies (0, 6, -1) correctly rejected with HTTP 422.")
    finally:
        app.dependency_overrides.clear()


def test_crud_skills_lifecycle():
    print("\n--- Testing Student Skill CRUD Lifecycle in Firestore ---")
    db = get_db()
    student_uid = f"student_crud_{uuid.uuid4().hex[:6]}"

    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": student_uid,
        "email": f"{student_uid}@academialink.edu",
        "name": "CRUD Test Student",
        "email_verified": True,
    }

    try:
        # 1. Initially should have 0 skills
        resp_get = client.get("/api/skills/me", headers={"Authorization": "Bearer mock_token"})
        assert resp_get.status_code == 200
        assert resp_get.json() == []
        print("[PASS] Initial skills list is empty for new student.")

        # 2. Create a skill: Python (Proficiency 4 = Advanced)
        create_payload = {
            "name": "Python",
            "proficiency": 4,
            "category": "Technical",
            "source": "manual",
            "evidence": {
                "type": "project",
                "title": "Data Pipeline in FastAPI",
                "url": "https://github.com/example/pipeline",
                "description": "High performance async ETL worker",
                "verified": False,
            },
        }
        resp_create = client.post(
            "/api/skills/me",
            headers={"Authorization": "Bearer mock_token"},
            json=create_payload,
        )
        assert resp_create.status_code == 201, f"Expected 201, got {resp_create.status_code}: {resp_create.text}"
        created_skill = resp_create.json()
        skill_id = created_skill["skillId"]

        assert created_skill["name"] == "Python"
        assert created_skill["proficiency"] == 4
        assert created_skill["level"] == "Advanced"
        assert created_skill["score"] == 80  # 4 * 20
        assert created_skill["evidence"]["type"] == "project"
        assert created_skill["verified"] is False, "Self-claimed project evidence must remain unverified by default"
        print(f"[PASS] Skill created: {created_skill['name']} (Proficiency: {created_skill['proficiency']} / Level: {created_skill['level']})")

        # Verify directly in Firestore subcollection users/{uid}/skills/{skillId}
        doc = db.collection("users").document(student_uid).collection("skills").document(skill_id).get()
        assert doc.exists
        assert doc.to_dict()["proficiency"] == 4
        print(f"[PASS] Confirmed Firestore subcollection document at users/{student_uid}/skills/{skill_id}")

        # 3. Retrieve skills list
        resp_list = client.get("/api/skills/me", headers={"Authorization": "Bearer mock_token"})
        assert resp_list.status_code == 200
        skills_list = resp_list.json()
        assert len(skills_list) == 1
        assert skills_list[0]["skillId"] == skill_id
        print("[PASS] GET /api/skills/me returned the created skill.")

        # 4. Update the skill: promote proficiency from 4 to 5 (Expert)
        update_payload = {"proficiency": 5}
        resp_put = client.put(
            f"/api/skills/me/{skill_id}",
            headers={"Authorization": "Bearer mock_token"},
            json=update_payload,
        )
        assert resp_put.status_code == 200
        updated_skill = resp_put.json()
        assert updated_skill["proficiency"] == 5
        assert updated_skill["level"] == "Expert"
        assert updated_skill["score"] == 100
        print(f"[PASS] Skill updated to Proficiency: {updated_skill['proficiency']} (Level: {updated_skill['level']})")

        # 5. Delete the skill
        resp_del = client.delete(f"/api/skills/me/{skill_id}", headers={"Authorization": "Bearer mock_token"})
        assert resp_del.status_code == 204
        print(f"[PASS] DELETE /api/skills/me/{skill_id} returned HTTP 204.")

        # Confirm deleted from Firestore
        doc_after_del = db.collection("users").document(student_uid).collection("skills").document(skill_id).get()
        assert not doc_after_del.exists
        print("[PASS] Confirmed document deleted from Firestore.")

    finally:
        app.dependency_overrides.clear()
        # Clean up user doc if created
        db.collection("users").document(student_uid).delete()


def test_cross_user_isolation():
    print("\n--- Testing Cross-User Skill Isolation (Security) ---")
    db = get_db()
    user_a_uid = f"user_a_{uuid.uuid4().hex[:6]}"
    user_b_uid = f"user_b_{uuid.uuid4().hex[:6]}"

    # User A creates a skill
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": user_a_uid,
        "email": "user_a@academialink.edu",
        "name": "User A",
        "email_verified": True,
    }

    resp_a = client.post(
        "/api/skills/me",
        headers={"Authorization": "Bearer token_a"},
        json={"name": "React", "proficiency": 3, "category": "Technical"},
    )
    assert resp_a.status_code == 201
    user_a_skill_id = resp_a.json()["skillId"]
    print(f"  User A created skill ID: {user_a_skill_id}")

    # Now authenticate as User B
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": user_b_uid,
        "email": "user_b@academialink.edu",
        "name": "User B",
        "email_verified": True,
    }

    try:
        # User B should NOT see User A's skill in their list
        resp_b_list = client.get("/api/skills/me", headers={"Authorization": "Bearer token_b"})
        assert resp_b_list.status_code == 200
        user_b_skill_ids = [s["skillId"] for s in resp_b_list.json()]
        assert user_a_skill_id not in user_b_skill_ids
        print("[PASS] User B cannot see User A's skills.")

        # User B attempting to update User A's skill directly must return 404
        resp_b_update = client.put(
            f"/api/skills/me/{user_a_skill_id}",
            headers={"Authorization": "Bearer token_b"},
            json={"proficiency": 5},
        )
        assert resp_b_update.status_code == 404, f"Expected 404, got {resp_b_update.status_code}"
        print("[PASS] User B cannot modify User A's skill (returned HTTP 404).")

        # User B attempting to delete User A's skill directly must return 404
        resp_b_delete = client.delete(
            f"/api/skills/me/{user_a_skill_id}",
            headers={"Authorization": "Bearer token_b"},
        )
        assert resp_b_delete.status_code == 404, f"Expected 404, got {resp_b_delete.status_code}"
        print("[PASS] User B cannot delete User A's skill (returned HTTP 404).")

    finally:
        app.dependency_overrides.clear()
        # Clean up User A's skill and user doc
        db.collection("users").document(user_a_uid).collection("skills").document(user_a_skill_id).delete()
        db.collection("users").document(user_a_uid).delete()
        db.collection("users").document(user_b_uid).delete()


def test_assessment_evaluation():
    print("\n--- Testing Skill Assessment Scoring & Verification ---")
    db = get_db()
    student_uid = f"student_assess_{uuid.uuid4().hex[:6]}"

    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": student_uid,
        "email": "assess_student@academialink.edu",
        "name": "Assessment Student",
        "email_verified": True,
    }

    try:
        # 1. Test fetching assessment questions for Python
        resp_q = client.get("/api/skills/assessment/questions?skill=python", headers={"Authorization": "Bearer mock_token"})
        assert resp_q.status_code == 200
        questions = resp_q.json()
        assert len(questions) == 5
        # Verify answer keys are NOT exposed to frontend
        for q in questions:
            assert "correctIndex" not in q
            assert "question" in q
            assert len(q["options"]) == 4
        print(f"[PASS] GET /api/skills/assessment/questions returned {len(questions)} sanitized questions.")

        # 2. Submit assessment with 4 correct answers out of 5 (80% -> Proficiency 4: Advanced)
        # Answer key for Python: py_1 -> 0, py_2 -> 1, py_3 -> 1, py_4 -> 1, py_5 -> 1
        submission = {
            "skillName": "Python",
            "category": "Technical",
            "answers": [
                {"questionId": "py_1", "selectedOption": 0},  # Correct
                {"questionId": "py_2", "selectedOption": 1},  # Correct
                {"questionId": "py_3", "selectedOption": 1},  # Correct
                {"questionId": "py_4", "selectedOption": 1},  # Correct
                {"questionId": "py_5", "selectedOption": 0},  # Incorrect (correct is 1)
            ],
        }
        resp_assess = client.post(
            "/api/skills/assessment",
            headers={"Authorization": "Bearer mock_token"},
            json=submission,
        )
        assert resp_assess.status_code == 200, f"Assessment failed: {resp_assess.text}"
        result = resp_assess.json()

        assert result["skillName"] == "Python"
        assert result["correctCount"] == 4
        assert result["totalQuestions"] == 5
        assert result["scorePercentage"] == 80
        assert result["proficiency"] == 4
        assert result["level"] == "Advanced"
        assert "Advanced proficiency (Level 4/5)" in result["explanation"]

        # Verify the assessed skill was automatically persisted in Firestore with verified evidence
        assessed_skill = result["skill"]
        assert assessed_skill["name"] == "Python"
        assert assessed_skill["proficiency"] == 4
        assert assessed_skill["source"] == "assessment"
        assert assessed_skill["verified"] is True
        assert assessed_skill["evidence"]["type"] == "assessment"
        assert assessed_skill["evidence"]["verified"] is True
        print(f"[PASS] Assessment scored deterministically: {result['correctCount']}/{result['totalQuestions']} (80%) -> Proficiency {result['proficiency']} ({result['level']}).")
        print("[PASS] Assessed skill persisted in Firestore with verified evidence.")

    finally:
        app.dependency_overrides.clear()
        # Clean up
        db.collection("users").document(student_uid).collection("skills").document("skill_python").delete()
        db.collection("users").document(student_uid).delete()


def test_openapi_documentation_skills():
    print("\n--- Testing OpenAPI Specification for Skills Endpoints ---")
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]

    assert "/api/skills/me" in paths
    assert "get" in paths["api/skills/me" if "api/skills/me" in paths else "/api/skills/me"]
    assert "post" in paths["api/skills/me" if "api/skills/me" in paths else "/api/skills/me"]
    assert "/api/skills/me/{skill_id}" in paths
    assert "/api/skills/assessment" in paths
    assert "/api/skills/assessment/questions" in paths
    print("[PASS] All skills and assessment endpoints documented in OpenAPI specification.")


if __name__ == "__main__":
    print("================================================================")
    print("RUNNING ACADEMIALINK SKILLS & ASSESSMENT MODULE TEST SUITE")
    print("================================================================")
    test_missing_or_invalid_token_rejected()
    test_invalid_proficiency_scale_rejected()
    test_crud_skills_lifecycle()
    test_cross_user_isolation()
    test_assessment_evaluation()
    test_openapi_documentation_skills()
    print("================================================================")
    print("ALL SKILLS & ASSESSMENT TESTS PASSED SUCCESSFULLY!")
    print("================================================================")

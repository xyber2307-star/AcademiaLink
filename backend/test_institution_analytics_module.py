"""
Comprehensive End-to-End Test Suite for STEP 34 — Institution Analytics Dashboard
Tests:
1. Security Guards, Token Verification & RBAC (HTTP 401 & 403 for students, recruiters, faculty)
2. Multi-Tenant Institution Scoping & Cross-Institution Access Isolation (HTTP 403 on parameter manipulation)
3. Deterministic Analytics Aggregation Accuracy (Validates exact mathematical counts & distributions)
4. Empty State Verification (Clean 0s, empty arrays, zero fabricated statistics)
5. Health Check & OpenAPI Documentation
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import verify_firebase_token
from app.firebase import get_db

client = TestClient(app)


def test_security_guards_and_token_verification():
    """
    Verify security guards and RBAC:
    - Missing token -> 401 Unauthorized
    - Student calling institution analytics -> 403 Forbidden
    - Recruiter calling institution analytics -> 403 Forbidden
    - Faculty calling institution analytics -> 403 Forbidden
    - Valid institution admin -> 200 OK
    """
    print("\n--- Testing Security Guards & RBAC for Institution Analytics ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_inst_g_{run_id}"
    recruiter_uid = f"recruiter_inst_g_{run_id}"
    faculty_uid = f"faculty_inst_g_{run_id}"
    inst_admin_uid = f"admin_inst_g_{run_id}"
    inst_id = f"inst_{run_id}"

    db.collection("users").document(student_uid).set({
        "uid": student_uid, "name": "Student User", "email": f"st_{run_id}@edu.org", "role": "student", "institution_id": inst_id
    })
    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid, "name": "Recruiter User", "email": f"rec_{run_id}@corp.com", "role": "recruiter"
    })
    db.collection("users").document(faculty_uid).set({
        "uid": faculty_uid, "name": "Faculty User", "email": f"fac_{run_id}@edu.org", "role": "faculty", "institution_id": inst_id
    })
    db.collection("users").document(inst_admin_uid).set({
        "uid": inst_admin_uid, "name": "Dean of Engineering", "email": f"dean_{run_id}@edu.org", "role": "institution", "institution_id": inst_id, "institution": "State University"
    })

    try:
        # 1. Missing Token -> 401
        resp_no_token = client.get("/api/institution/analytics")
        assert resp_no_token.status_code == 401, f"Expected 401, got {resp_no_token.status_code}"

        # 2. Student Role -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_uid, "email": f"st_{run_id}@edu.org"}
        resp_student = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp_student.status_code == 403, f"Expected 403 for student, got {resp_student.status_code}"

        # 3. Recruiter Role -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": recruiter_uid, "email": f"rec_{run_id}@corp.com"}
        resp_recruiter = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp_recruiter.status_code == 403, f"Expected 403 for recruiter, got {resp_recruiter.status_code}"

        # 4. Faculty Role -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": faculty_uid, "email": f"fac_{run_id}@edu.org"}
        resp_faculty = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp_faculty.status_code == 403, f"Expected 403 for faculty, got {resp_faculty.status_code}"

        # 5. Valid Institution Admin -> 200
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": inst_admin_uid, "email": f"dean_{run_id}@edu.org"}
        resp_admin = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp_admin.status_code == 200, f"Expected 200 for institution admin, got {resp_admin.status_code}: {resp_admin.text}"
        data = resp_admin.json()
        assert data["institution_id"] == inst_id
        assert data["institution_name"] == "State University"

        print("[PASS] Security guards and RBAC strictly prevent unauthorized access to institution analytics.")
    finally:
        app.dependency_overrides.clear()
        for uid in [student_uid, recruiter_uid, faculty_uid, inst_admin_uid]:
            db.collection("users").document(uid).delete()


def test_institution_scoping_and_cross_institution_isolation():
    """
    Verify multi-tenant scoping:
    - Admin of Institution A CANNOT query Institution B's data via query param (403 Forbidden)
    - Admin of Institution A CAN query Institution A (200 OK)
    - System Admin (role: admin) can query specific institution (200 OK)
    """
    print("\n--- Testing Institution Scoping & Multi-Tenant Isolation ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    inst_a = f"inst_a_{run_id}"
    inst_b = f"inst_b_{run_id}"
    admin_a_uid = f"admin_a_{run_id}"
    sys_admin_uid = f"sys_admin_{run_id}"

    db.collection("users").document(admin_a_uid).set({
        "uid": admin_a_uid, "name": "Dean Alpha", "email": f"alpha_{run_id}@inst_a.edu", "role": "institution", "institution_id": inst_a
    })
    db.collection("users").document(sys_admin_uid).set({
        "uid": sys_admin_uid, "name": "System Administrator", "email": f"sys_{run_id}@platform.org", "role": "admin"
    })

    try:
        # 1. Admin A attempts to request Institution B analytics -> 403 Forbidden!
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": admin_a_uid, "email": f"alpha_{run_id}@inst_a.edu"}
        resp_cross = client.get(
            f"/api/institution/analytics?institution_id={inst_b}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_cross.status_code == 403, f"Expected 403 on cross-institution parameter tamper, got {resp_cross.status_code}"

        # 2. Admin A requests own institution -> 200 OK
        resp_own = client.get(
            f"/api/institution/analytics?institution_id={inst_a}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_own.status_code == 200
        assert resp_own.json()["institution_id"] == inst_a

        # 3. System Admin requests Institution B -> 200 OK
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": sys_admin_uid, "email": f"sys_{run_id}@platform.org"}
        resp_sys = client.get(
            f"/api/institution/analytics?institution_id={inst_b}",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp_sys.status_code == 200
        assert resp_sys.json()["institution_id"] == inst_b

        print("[PASS] Institution scoping strictly prevents cross-tenant data access.")
    finally:
        app.dependency_overrides.clear()
        for uid in [admin_a_uid, sys_admin_uid]:
            db.collection("users").document(uid).delete()


def test_analytics_aggregation_accuracy():
    """
    Verify deterministic analytics calculations from genuine Firestore data:
    - 2 students for target institution (Student 1, Student 2)
    - 1 foreign student from another institution (must NOT be counted)
    - Verify exact skill counts, proficiency distribution, evidence status counts, and learning paths
    """
    print("\n--- Testing Analytics Aggregation Accuracy & Integrity ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    inst_id = f"inst_acc_{run_id}"
    admin_uid = f"admin_acc_{run_id}"
    student_1 = f"s1_acc_{run_id}"
    student_2 = f"s2_acc_{run_id}"
    student_other = f"s_other_acc_{run_id}"
    asgn_id = f"asgn_acc_{run_id}"
    path_id = f"lp_acc_{run_id}"
    ev1_id = f"ev1_acc_{run_id}"
    ev2_id = f"ev2_acc_{run_id}"
    fb_id = f"fb_acc_{run_id}"

    # Setup Institution Admin
    db.collection("users").document(admin_uid).set({
        "uid": admin_uid, "name": "Institute Director", "email": f"dir_{run_id}@institute.edu", "role": "institution", "institution_id": inst_id, "institution": "Tech Institute"
    })

    # Setup 2 Students for this institution
    db.collection("users").document(student_1).set({
        "uid": student_1, "name": "Alice Target", "email": f"alice_{run_id}@institute.edu", "role": "student", "institution_id": inst_id, "profileCompletion": 50
    })
    db.collection("users").document(student_2).set({
        "uid": student_2, "name": "Bob Target", "email": f"bob_{run_id}@institute.edu", "role": "student", "institution_id": inst_id, "profileCompletion": 25
    })

    # Setup 1 Student for a different institution (must NOT be counted)
    db.collection("users").document(student_other).set({
        "uid": student_other, "name": "Foreign Student", "email": f"foreign_{run_id}@other.edu", "role": "student", "institution_id": "other_inst"
    })

    # Student 1 Skills: Python (proficiency=4 / Advanced), SQL (proficiency=3 / Intermediate)
    db.collection("users").document(student_1).collection("skills").document("py").set({
        "name": "Python", "proficiency": 4, "category": "Technical"
    })
    db.collection("users").document(student_1).collection("skills").document("sql").set({
        "name": "SQL", "proficiency": 3, "category": "Technical"
    })

    # Student 2 Skills: Python (proficiency=2 / Basic)
    db.collection("users").document(student_2).collection("skills").document("py").set({
        "name": "Python", "proficiency": 2, "category": "Technical"
    })

    # Foreign Student Skill (must not be counted)
    db.collection("users").document(student_other).collection("skills").document("py").set({
        "name": "Python", "proficiency": 5, "category": "Technical"
    })

    # Student 1 Learning Path
    db.collection("users").document(student_1).collection("learning_paths").document(path_id).set({
        "path_id": path_id, "target_job_title": "Cloud Architect", "target_company": "CloudCorp", "status": "active",
        "skills": [
            {"skill_name": "Python", "current_proficiency": 4, "required_proficiency": 5, "gap": 1.0, "priority": "High", "status": "in_progress"}
        ]
    })

    # Student 1 Evidence (Approved)
    db.collection("users").document(student_1).collection("evidence").document(ev1_id).set({
        "evidence_id": ev1_id, "type": "project", "title": "Scalable Streaming", "verification_status": "approved"
    })

    # Student 2 Evidence (Pending)
    db.collection("users").document(student_2).collection("evidence").document(ev2_id).set({
        "evidence_id": ev2_id, "type": "certificate", "title": "SQL Basics", "verification_status": "pending"
    })

    # Mentor Assignment for Student 1
    db.collection("mentor_assignments").document(asgn_id).set({
        "assignment_id": asgn_id, "mentor_uid": "prof_mentor", "student_uid": student_1, "institution_id": inst_id, "status": "active"
    })

    # Feedback for Student 1
    db.collection("users").document(student_1).collection("mentor_feedback").document(fb_id).set({
        "feedback_id": fb_id, "message": "Keep up the great work with distributed systems."
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": admin_uid, "email": f"dir_{run_id}@institute.edu"}
        resp = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # 1. Student Overview
        so = data["student_overview"]
        assert so["total_students"] == 2, f"Expected 2 students for this institution, got {so['total_students']}"
        assert so["students_with_skills"] == 2
        assert so["students_with_learning_paths"] == 1
        assert so["active_students"] == 2

        # 2. Skill Analytics
        sk = data["skill_analytics"]
        assert sk["total_skills_recorded"] == 3  # 2 for student 1, 1 for student 2 (foreign student excluded)
        # Most common skill: Python (count=2, avg proficiency = (4+2)/2 = 3.0)
        py_stat = next((s for s in sk["most_common_skills"] if s["name"] == "Python"), None)
        assert py_stat is not None
        assert py_stat["count"] == 2
        assert py_stat["average_proficiency"] == 3.0

        # Proficiency distribution: 1 Beginner, 1 Basic (Python=2), 1 Intermediate (SQL=3), 1 Advanced (Python=4), 0 Expert
        pd = sk["proficiency_distribution"]
        assert pd["Basic"] == 1
        assert pd["Intermediate"] == 1
        assert pd["Advanced"] == 1
        assert pd["Expert"] == 0

        # 3. Learning Analytics
        la = data["learning_analytics"]
        assert la["total_learning_paths"] == 1
        assert la["paths_by_status"]["active"] == 1
        assert la["skills_by_status"]["in_progress"] == 1

        # 4. Evidence Analytics
        ea = data["evidence_analytics"]
        assert ea["total_evidence_submissions"] == 2
        assert ea["evidence_by_status"]["approved"] == 1
        assert ea["evidence_by_status"]["pending"] == 1
        assert ea["evidence_by_status"]["rejected"] == 0

        # 5. Mentorship Analytics
        ma = data["mentorship_analytics"]
        assert ma["total_mentor_assignments"] == 1
        assert ma["active_mentor_assignments"] == 1
        assert ma["assigned_students_count"] == 1
        assert ma["feedback_activity_count"] == 1
        assert ma["pending_evidence_reviews"] == 1

        print("[PASS] Exact mathematical accuracy verified on all aggregated Firestore analytics metrics.")
    finally:
        app.dependency_overrides.clear()
        # Clean up
        db.collection("mentor_assignments").document(asgn_id).delete()
        db.collection("users").document(student_1).collection("skills").document("py").delete()
        db.collection("users").document(student_1).collection("skills").document("sql").delete()
        db.collection("users").document(student_1).collection("learning_paths").document(path_id).delete()
        db.collection("users").document(student_1).collection("evidence").document(ev1_id).delete()
        db.collection("users").document(student_1).collection("mentor_feedback").document(fb_id).delete()

        db.collection("users").document(student_2).collection("skills").document("py").delete()
        db.collection("users").document(student_2).collection("evidence").document(ev2_id).delete()

        db.collection("users").document(student_other).collection("skills").document("py").delete()

        for uid in [admin_uid, student_1, student_2, student_other]:
            db.collection("users").document(uid).delete()


def test_empty_institution_analytics():
    """
    Verify zero fake data handling:
    - Institution with zero students returns total_students=0, empty arrays, and 0 metrics.
    - No fabricated statistics.
    """
    print("\n--- Testing Empty Institution Analytics ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    empty_inst = f"empty_inst_{run_id}"
    admin_uid = f"admin_empty_{run_id}"

    db.collection("users").document(admin_uid).set({
        "uid": admin_uid, "name": "Empty Institute Admin", "email": f"empty_{run_id}@edu.org", "role": "institution", "institution_id": empty_inst
    })

    try:
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": admin_uid, "email": f"empty_{run_id}@edu.org"}
        resp = client.get("/api/institution/analytics", headers={"Authorization": "Bearer mock_token"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["student_overview"]["total_students"] == 0
        assert data["student_overview"]["active_students"] == 0
        assert data["skill_analytics"]["total_skills_recorded"] == 0
        assert len(data["skill_analytics"]["most_common_skills"]) == 0
        assert data["evidence_analytics"]["total_evidence_submissions"] == 0
        assert data["mentorship_analytics"]["total_mentor_assignments"] == 0

        print("[PASS] Clean zero metrics and zero fake data confirmed for empty institution.")
    finally:
        app.dependency_overrides.clear()
        db.collection("users").document(admin_uid).delete()


def test_health_and_openapi_docs():
    """Verify GET /api/health and presence of institution endpoint in OpenAPI schema."""
    print("\n--- Testing Health & OpenAPI Documentation ---")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("status") in ["healthy", "degraded"]

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    paths = openapi_resp.json().get("paths", {})
    assert "/api/institution/analytics" in paths
    print("[PASS] Health endpoint healthy and /api/institution/analytics documented in OpenAPI.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

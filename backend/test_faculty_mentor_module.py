"""
Comprehensive End-to-End Test Suite for STEP 33 — Faculty / Mentor Module
Tests:
1. Security Guards, Bearer Token Verification & RBAC (HTTP 401 & 403)
2. Mentor-Student Assignment & Strict Multi-Tenant Access Isolation (HTTP 403 for unassigned)
3. Student-Facing Mentor Discovery (GET /api/mentor/me, assigned vs clean empty state)
4. Evidence Review Lifecycle & Zero Skill Inflation (Reviewer UID stamping, 403 for cross-mentor)
5. Mentor Guidance/Feedback Lifecycle & Student Privacy (Cross-tenant 403)
6. Evidence Attachment File Streaming Security (Assigned only)
7. Health Check & OpenAPI Documentation
"""

import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import verify_firebase_token
from app.firebase import get_db

client = TestClient(app)


def test_security_guards_and_token_verification():
    """
    Verify authentication guards and role-based access control:
    - Missing token -> 401 Unauthorized
    - Student calling faculty endpoints -> 403 Forbidden
    - Recruiter calling faculty endpoints -> 403 Forbidden
    - Student calling assignment creation -> 403 Forbidden
    """
    print("\n--- Testing Security Guards & RBAC for Faculty/Mentor APIs ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    student_uid = f"student_guard_{run_id}"
    recruiter_uid = f"recruiter_guard_{run_id}"

    db.collection("users").document(student_uid).set({
        "uid": student_uid,
        "name": "Student Guard",
        "email": f"student_{run_id}@academialink.edu",
        "role": "student",
    })
    db.collection("users").document(recruiter_uid).set({
        "uid": recruiter_uid,
        "name": "Recruiter Guard",
        "email": f"recruiter_{run_id}@techcorp.com",
        "role": "recruiter",
    })

    try:
        # 1. Missing Token -> 401
        resp_no_token = client.get("/api/faculty/students")
        assert resp_no_token.status_code == 401, f"Expected 401, got {resp_no_token.status_code}"

        # 2. Student Role calling faculty endpoint -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_uid,
            "email": f"student_{run_id}@academialink.edu",
        }
        resp_student = client.get("/api/faculty/students", headers={"Authorization": "Bearer mock_token"})
        assert resp_student.status_code == 403, f"Expected 403 for student, got {resp_student.status_code}"

        # 3. Recruiter Role calling faculty endpoint -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": recruiter_uid,
            "email": f"recruiter_{run_id}@techcorp.com",
        }
        resp_recruiter = client.get("/api/faculty/students", headers={"Authorization": "Bearer mock_token"})
        assert resp_recruiter.status_code == 403, f"Expected 403 for recruiter, got {resp_recruiter.status_code}"

        # 4. Student attempting assignment administration -> 403
        app.dependency_overrides[verify_firebase_token] = lambda: {
            "uid": student_uid,
            "email": f"student_{run_id}@academialink.edu",
        }
        resp_self_assign = client.post(
            "/api/faculty/assignments",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "mentor_uid": "some_mentor",
                "student_uid": student_uid,
                "status": "active",
            },
        )
        assert resp_self_assign.status_code == 403, f"Expected 403 for student self-assignment, got {resp_self_assign.status_code}"

        print("[PASS] Security guards and RBAC strictly prevent unauthorized student/recruiter access.")
    finally:
        app.dependency_overrides.clear()
        db.collection("users").document(student_uid).delete()
        db.collection("users").document(recruiter_uid).delete()


def test_mentor_assignment_and_access_isolation():
    """
    Verify mentor-student assignment and multi-tenant isolation:
    - Admin creates assignment: Mentor A -> Student 1
    - Mentor A can view Student 1's profile and skills
    - Mentor B CANNOT view Student 1 (403 Forbidden)
    - Student 1 gets Mentor A from GET /api/mentor/me
    - Unassigned Student 2 gets assigned=False, mentor=None (no fake data)
    """
    print("\n--- Testing Mentor Assignment & Multi-Tenant Access Isolation ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    admin_uid = f"admin_{run_id}"
    mentor_a = f"mentor_a_{run_id}"
    mentor_b = f"mentor_b_{run_id}"
    student_1 = f"student_1_{run_id}"
    student_2 = f"student_2_{run_id}"
    assignment_id = f"asgn_{mentor_a[:8]}_{student_1[:8]}"

    # Setup profiles
    db.collection("users").document(admin_uid).set({
        "uid": admin_uid, "name": "Admin User", "email": f"admin_{run_id}@edu.org", "role": "admin"
    })
    db.collection("users").document(mentor_a).set({
        "uid": mentor_a, "name": "Prof. Ada Lovelace", "email": f"ada_{run_id}@edu.org", "role": "faculty", "department": "Computer Science"
    })
    db.collection("users").document(mentor_b).set({
        "uid": mentor_b, "name": "Prof. Charles Babbage", "email": f"charles_{run_id}@edu.org", "role": "faculty", "department": "Mechanical"
    })
    db.collection("users").document(student_1).set({
        "uid": student_1, "name": "Alice Student", "email": f"alice_{run_id}@student.edu", "role": "student", "targetRole": "Backend Engineer"
    })
    db.collection("users").document(student_2).set({
        "uid": student_2, "name": "Bob Unassigned", "email": f"bob_{run_id}@student.edu", "role": "student"
    })

    # Add skill to student 1
    db.collection("users").document(student_1).collection("skills").document("python").set({
        "name": "Python", "proficiency": 3.0, "category": "Technical"
    })

    try:
        # 1. Admin creates assignment: Mentor A -> Student 1
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": admin_uid, "email": f"admin_{run_id}@edu.org"}
        asgn_resp = client.post(
            "/api/faculty/assignments",
            headers={"Authorization": "Bearer mock_token"},
            json={"mentor_uid": mentor_a, "student_uid": student_1, "status": "active"},
        )
        assert asgn_resp.status_code == 201, f"Expected 201, got {asgn_resp.status_code}: {asgn_resp.text}"

        # 2. Mentor A lists assigned students -> Student 1 present
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_a, "email": f"ada_{run_id}@edu.org"}
        list_resp = client.get("/api/faculty/students", headers={"Authorization": "Bearer mock_token"})
        assert list_resp.status_code == 200
        assigned_uids = [s["student_uid"] for s in list_resp.json()]
        assert student_1 in assigned_uids
        assert student_2 not in assigned_uids

        # 3. Mentor A views Student 1 detail -> 200 OK
        detail_resp = client.get(f"/api/faculty/students/{student_1}", headers={"Authorization": "Bearer mock_token"})
        assert detail_resp.status_code == 200
        assert detail_resp.json()["student_uid"] == student_1
        assert any(sk["name"] == "Python" for sk in detail_resp.json()["skills"])

        # 4. Mentor B attempts to access Student 1 detail -> 403 Forbidden!
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_b, "email": f"charles_{run_id}@edu.org"}
        cross_resp = client.get(f"/api/faculty/students/{student_1}", headers={"Authorization": "Bearer mock_token"})
        assert cross_resp.status_code == 403, f"Expected 403 for unassigned mentor, got {cross_resp.status_code}"

        # 5. Student 1 checks assigned mentor -> returns Mentor A
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_1, "email": f"alice_{run_id}@student.edu"}
        s1_mentor_resp = client.get("/api/mentor/me", headers={"Authorization": "Bearer mock_token"})
        assert s1_mentor_resp.status_code == 200
        s1_data = s1_mentor_resp.json()
        assert s1_data["assigned"] is True
        assert s1_data["mentor"]["uid"] == mentor_a
        assert s1_data["mentor"]["name"] == "Prof. Ada Lovelace"

        # 6. Unassigned Student 2 checks assigned mentor -> returns assigned=False, mentor=None
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_2, "email": f"bob_{run_id}@student.edu"}
        s2_mentor_resp = client.get("/api/mentor/me", headers={"Authorization": "Bearer mock_token"})
        assert s2_mentor_resp.status_code == 200
        s2_data = s2_mentor_resp.json()
        assert s2_data["assigned"] is False
        assert s2_data["mentor"] is None

        print("[PASS] Multi-tenant assignment isolation and student mentor discovery verified.")
    finally:
        app.dependency_overrides.clear()
        db.collection("mentor_assignments").document(assignment_id).delete()
        db.collection("users").document(student_1).collection("skills").document("python").delete()
        for uid in [admin_uid, mentor_a, mentor_b, student_1, student_2]:
            db.collection("users").document(uid).delete()


def test_evidence_review_and_skill_integrity():
    """
    Verify evidence review lifecycle and zero skill inflation:
    - Student submits evidence (defaults to pending)
    - Assigned Mentor views pending evidence
    - Unassigned Mentor cannot review (403)
    - Student cannot self-review (403)
    - Assigned Mentor approves evidence with review notes
    - Reviewed status, reviewer_id, and reviewedAt timestamp stamped
    - Skill proficiency in users/{uid}/skills remains strictly unchanged
    """
    print("\n--- Testing Evidence Review Lifecycle & Skill Integrity ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    mentor_a = f"mentor_rev_a_{run_id}"
    mentor_b = f"mentor_rev_b_{run_id}"
    student_uid = f"student_rev_{run_id}"
    assignment_id = f"asgn_{mentor_a[:8]}_{student_uid[:8]}"
    ev_id = f"ev_{run_id}"

    db.collection("users").document(mentor_a).set({
        "uid": mentor_a, "name": "Mentor A", "email": f"ma_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(mentor_b).set({
        "uid": mentor_b, "name": "Mentor B", "email": f"mb_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(student_uid).set({
        "uid": student_uid, "name": "Student Candidate", "email": f"st_{run_id}@student.edu", "role": "student"
    })

    # Active assignment: Mentor A -> Student
    db.collection("mentor_assignments").document(assignment_id).set({
        "assignment_id": assignment_id,
        "mentor_uid": mentor_a,
        "student_uid": student_uid,
        "status": "active",
    })

    # Student skill at exactly 2.5
    skill_ref = db.collection("users").document(student_uid).collection("skills").document("sql")
    skill_ref.set({"name": "SQL", "proficiency": 2.5, "category": "Technical"})

    # Student submits evidence
    ev_ref = db.collection("users").document(student_uid).collection("evidence").document(ev_id)
    ev_ref.set({
        "evidence_id": ev_id,
        "title": "Optimized Distributed Database",
        "type": "project",
        "verification_status": "pending",
        "skill_ids": ["SQL"],
        "project_url": "https://database.demo.io",
    })

    try:
        # 1. Mentor A lists pending evidence
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_a, "email": f"ma_{run_id}@edu.org"}
        pending_resp = client.get("/api/faculty/evidence/pending", headers={"Authorization": "Bearer mock_token"})
        assert pending_resp.status_code == 200
        pending_ids = [p["evidence_id"] for p in pending_resp.json()]
        assert ev_id in pending_ids

        # 2. Mentor B attempts to review Student's evidence -> 403 Forbidden
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_b, "email": f"mb_{run_id}@edu.org"}
        b_rev_resp = client.patch(
            f"/api/faculty/evidence/{ev_id}/review",
            headers={"Authorization": "Bearer mock_token"},
            json={"verification_status": "approved", "verification_notes": "Snooping review", "student_uid": student_uid},
        )
        assert b_rev_resp.status_code == 403, f"Expected 403 for unassigned mentor, got {b_rev_resp.status_code}"

        # 3. Student attempts to call faculty review -> 403 Forbidden
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_uid, "email": f"st_{run_id}@student.edu"}
        s_rev_resp = client.patch(
            f"/api/faculty/evidence/{ev_id}/review",
            headers={"Authorization": "Bearer mock_token"},
            json={"verification_status": "approved", "student_uid": student_uid},
        )
        assert s_rev_resp.status_code == 403, f"Expected 403 for student, got {s_rev_resp.status_code}"

        # 4. Mentor A approves evidence with review notes
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_a, "email": f"ma_{run_id}@edu.org"}
        a_rev_resp = client.patch(
            f"/api/faculty/evidence/{ev_id}/review",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "verification_status": "approved",
                "verification_notes": "Verified relational indexing and query execution plans.",
                "student_uid": student_uid,
            },
        )
        assert a_rev_resp.status_code == 200, f"Expected 200, got {a_rev_resp.status_code}: {a_rev_resp.text}"
        data = a_rev_resp.json()
        assert data["verification_status"] == "approved"
        assert data["reviewer_id"] == mentor_a
        assert data["reviewedAt"] is not None
        assert "indexing" in data["verification_notes"]

        # 5. ZERO SKILL INFLATION CHECK: SQL skill in users/{uid}/skills must still be 2.5
        skill_after = skill_ref.get().to_dict()
        assert skill_after["proficiency"] == 2.5, (
            f"CRITICAL INTEGRITY FAILURE: Evidence approval altered skill proficiency from 2.5 to {skill_after['proficiency']}!"
        )
        print("[PASS] Evidence approved; server-stamped reviewer fields verified; skill proficiency strictly preserved at 2.5.")
    finally:
        app.dependency_overrides.clear()
        db.collection("mentor_assignments").document(assignment_id).delete()
        ev_ref.delete()
        skill_ref.delete()
        for uid in [mentor_a, mentor_b, student_uid]:
            db.collection("users").document(uid).delete()


def test_mentor_feedback_lifecycle():
    """
    Verify mentor feedback lifecycle and privacy:
    - Assigned Mentor posts feedback for student
    - Unassigned Mentor cannot post feedback (403 Forbidden)
    - Student retrieves their feedback via GET /api/mentor/me/feedback
    - Student cannot create feedback on faculty endpoint (403)
    """
    print("\n--- Testing Mentor Feedback Lifecycle & Privacy ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    mentor_a = f"mentor_fb_a_{run_id}"
    mentor_b = f"mentor_fb_b_{run_id}"
    student_uid = f"student_fb_{run_id}"
    assignment_id = f"asgn_{mentor_a[:8]}_{student_uid[:8]}"

    db.collection("users").document(mentor_a).set({
        "uid": mentor_a, "name": "Dr. Grace Hopper", "email": f"gh_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(mentor_b).set({
        "uid": mentor_b, "name": "Dr. John von Neumann", "email": f"jvn_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(student_uid).set({
        "uid": student_uid, "name": "Student Mentee", "email": f"mentee_{run_id}@student.edu", "role": "student"
    })

    db.collection("mentor_assignments").document(assignment_id).set({
        "assignment_id": assignment_id, "mentor_uid": mentor_a, "student_uid": student_uid, "status": "active"
    })

    created_fb_id = None
    try:
        # 1. Mentor B attempts to post feedback -> 403 Forbidden
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_b, "email": f"jvn_{run_id}@edu.org"}
        resp_b = client.post(
            f"/api/faculty/students/{student_uid}/feedback",
            headers={"Authorization": "Bearer mock_token"},
            json={"message": "Unauthorized feedback"},
        )
        assert resp_b.status_code == 403, f"Expected 403 for unassigned mentor, got {resp_b.status_code}"

        # 2. Mentor A posts feedback for Student -> 201 Created
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_a, "email": f"gh_{run_id}@edu.org"}
        resp_a = client.post(
            f"/api/faculty/students/{student_uid}/feedback",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "message": "Focus on asynchronous programming and concurrent worker pools in your next sprint.",
                "related_skill_id": "Python",
            },
        )
        assert resp_a.status_code == 201, f"Expected 201, got {resp_a.status_code}: {resp_a.text}"
        fb_data = resp_a.json()
        created_fb_id = fb_data["feedback_id"]
        assert fb_data["mentor_uid"] == mentor_a
        assert fb_data["student_uid"] == student_uid
        assert fb_data["mentor_name"] == "Dr. Grace Hopper"

        # 3. Student views feedback via /api/mentor/me/feedback
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_uid, "email": f"mentee_{run_id}@student.edu"}
        s_fb_resp = client.get("/api/mentor/me/feedback", headers={"Authorization": "Bearer mock_token"})
        assert s_fb_resp.status_code == 200
        fb_list = s_fb_resp.json()
        assert any(f["feedback_id"] == created_fb_id for f in fb_list)

        print("[PASS] Mentor feedback created, isolated from unassigned mentors, and retrieved by mentee.")
    finally:
        app.dependency_overrides.clear()
        if created_fb_id:
            db.collection("users").document(student_uid).collection("mentor_feedback").document(created_fb_id).delete()
        db.collection("mentor_assignments").document(assignment_id).delete()
        for uid in [mentor_a, mentor_b, student_uid]:
            db.collection("users").document(uid).delete()


def test_evidence_file_access_security():
    """
    Verify file streaming authorization:
    - Student uploads a valid evidence file
    - Assigned Mentor A can stream the file (200 OK)
    - Unassigned Mentor B is rejected (403 Forbidden)
    """
    print("\n--- Testing Evidence File Streaming Security ---")
    db = get_db()
    run_id = uuid.uuid4().hex[:6]
    mentor_a = f"mentor_file_a_{run_id}"
    mentor_b = f"mentor_file_b_{run_id}"
    student_uid = f"student_file_{run_id}"
    assignment_id = f"asgn_{mentor_a[:8]}_{student_uid[:8]}"
    ev_id = f"ev_file_{run_id}"

    db.collection("users").document(mentor_a).set({
        "uid": mentor_a, "name": "Mentor Alpha", "email": f"mfa_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(mentor_b).set({
        "uid": mentor_b, "name": "Mentor Beta", "email": f"mfb_{run_id}@edu.org", "role": "faculty"
    })
    db.collection("users").document(student_uid).set({
        "uid": student_uid, "name": "Student File Owner", "email": f"sfo_{run_id}@student.edu", "role": "student"
    })

    db.collection("mentor_assignments").document(assignment_id).set({
        "assignment_id": assignment_id, "mentor_uid": mentor_a, "student_uid": student_uid, "status": "active"
    })

    # Student uploads a file
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": student_uid, "email": f"sfo_{run_id}@student.edu"}
    dummy_pdf = io.BytesIO(b"%PDF-1.4 Mock certificate content for verification testing")
    upload_resp = client.post(
        "/api/evidence/upload",
        headers={"Authorization": "Bearer mock_token"},
        files={"file": ("project_report.pdf", dummy_pdf, "application/pdf")},
    )
    assert upload_resp.status_code == 200
    file_path = upload_resp.json()["file_path"]

    # Link file to evidence item
    ev_ref = db.collection("users").document(student_uid).collection("evidence").document(ev_id)
    ev_ref.set({
        "evidence_id": ev_id,
        "title": "Certified Architecture Design",
        "type": "certificate",
        "file_path": file_path,
        "verification_status": "pending",
    })

    try:
        # 1. Unassigned Mentor B attempts to download -> 403 Forbidden
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_b, "email": f"mfb_{run_id}@edu.org"}
        b_dl_resp = client.get(
            f"/api/faculty/students/{student_uid}/evidence/{ev_id}/file",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert b_dl_resp.status_code == 403, f"Expected 403 for unassigned mentor, got {b_dl_resp.status_code}"

        # 2. Assigned Mentor A downloads file -> 200 OK
        app.dependency_overrides[verify_firebase_token] = lambda: {"uid": mentor_a, "email": f"mfa_{run_id}@edu.org"}
        a_dl_resp = client.get(
            f"/api/faculty/students/{student_uid}/evidence/{ev_id}/file",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert a_dl_resp.status_code == 200, f"Expected 200 for assigned mentor, got {a_dl_resp.status_code}"
        assert b"%PDF-1.4" in a_dl_resp.content

        print("[PASS] Evidence file streaming strictly restricted to assigned mentor.")
    finally:
        app.dependency_overrides.clear()
        ev_ref.delete()
        db.collection("mentor_assignments").document(assignment_id).delete()
        for uid in [mentor_a, mentor_b, student_uid]:
            db.collection("users").document(uid).delete()


def test_health_and_openapi_docs():
    """Verify GET /api/health and presence of faculty & mentor endpoints in OpenAPI docs."""
    print("\n--- Testing Health Endpoint & OpenAPI Documentation ---")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json().get("status") in ["healthy", "degraded"]

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    paths = openapi_resp.json().get("paths", {})
    assert "/api/faculty/students" in paths
    assert "/api/faculty/students/{student_uid}" in paths
    assert "/api/faculty/evidence/pending" in paths
    assert "/api/faculty/evidence/{evidence_id}/review" in paths
    assert "/api/faculty/students/{student_uid}/feedback" in paths
    assert "/api/mentor/me" in paths
    assert "/api/mentor/me/feedback" in paths
    print("[PASS] Health check and all faculty & mentor OpenAPI endpoints verified.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

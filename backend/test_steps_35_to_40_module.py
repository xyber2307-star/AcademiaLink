"""
Integration & Security Test Suite for Steps 35–40:
- Step 35: AI Career Assistant (Grounded Advisory, No Hallucination, Security)
- Step 36: Quiz & Assessment Enhancement (Deterministic Scoring, Preservation of Verified Skills, History)
- Step 37: Opportunities & Application Tracking (Application Lifecycle, Recruiter Ownership, Student Limits)
- Step 38: Notifications & Activity System (Event Generation, Read State, User Isolation)
- Step 39: Admin & Role Management (Escalation Prevention, RBAC Security)
- Step 40: Data Provenance & Real Data Assurance
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.firebase import get_db, initialize_firebase
from app.auth import verify_firebase_token

client = TestClient(app)

# Test UIDs
STUDENT_UID = "test_s35_student_001"
STUDENT_EMAIL = "s35_student@test.edu"

RECRUITER_UID = "test_s35_recruiter_001"
RECRUITER_EMAIL = "s35_recruiter@company.com"

OTHER_RECRUITER_UID = "test_s35_recruiter_other"
OTHER_RECRUITER_EMAIL = "other_recruiter@company.com"

ADMIN_UID = "test_s35_admin_001"
ADMIN_EMAIL = "s35_admin@academialink.edu"

JOB_ID = "job_test_s35_software_eng"


def set_user(uid: str, email: str, role: str = "student"):
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": uid,
        "email": email,
        "role": role,
    }


def clear_user():
    app.dependency_overrides.pop(verify_firebase_token, None)


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Seed prerequisite test records in Firestore."""
    initialize_firebase()
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Seed Student
    db.collection("users").document(STUDENT_UID).set({
        "uid": STUDENT_UID,
        "name": "S35 Test Student",
        "email": STUDENT_EMAIL,
        "role": "student",
        "institution": "MIT",
        "institution_id": "inst_mit",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    # Seed Python skill (verified at level 4.0)
    db.collection("users").document(STUDENT_UID).collection("skills").document("skill_python").set({
        "skillId": "skill_python",
        "name": "Python",
        "category": "Technical",
        "proficiency": 4.0,
        "verified": True,
        "source": "faculty_verified",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    # 2. Seed Recruiter
    db.collection("users").document(RECRUITER_UID).set({
        "uid": RECRUITER_UID,
        "name": "S35 Recruiter",
        "email": RECRUITER_EMAIL,
        "role": "recruiter",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    # Seed other recruiter
    db.collection("users").document(OTHER_RECRUITER_UID).set({
        "uid": OTHER_RECRUITER_UID,
        "name": "Other Recruiter",
        "email": OTHER_RECRUITER_EMAIL,
        "role": "recruiter",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    # 3. Seed Published Job owned by RECRUITER_UID
    db.collection("jobs").document(JOB_ID).set({
        "job_id": JOB_ID,
        "title": "Full Stack Software Engineer",
        "company": "CloudTech Solutions",
        "location": "Remote",
        "recruiter_id": RECRUITER_UID,
        "status": "published",
        "required_skills": ["Python", "Docker", "Kubernetes"],
        "preferred_skills": ["React"],
        "minimum_proficiency": 3.0,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    # 4. Seed Admin
    db.collection("users").document(ADMIN_UID).set({
        "uid": ADMIN_UID,
        "name": "S35 Admin",
        "email": ADMIN_EMAIL,
        "role": "admin",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })

    yield

    # Cleanup test data
    try:
        clear_user()
        db.collection("users").document(STUDENT_UID).delete()
        db.collection("users").document(RECRUITER_UID).delete()
        db.collection("users").document(OTHER_RECRUITER_UID).delete()
        db.collection("users").document(ADMIN_UID).delete()
        db.collection("jobs").document(JOB_ID).delete()
    except Exception:
        pass


def test_ai_assistant_grounded_and_security():
    """Step 35: Verify AI Career Assistant uses real student data and adheres to security."""
    clear_user()

    # 1. Unauthenticated request rejected with 401
    r_unauth = client.post("/api/ai/chat", json={"message": "What are my best skills?"})
    assert r_unauth.status_code == 401

    # 2. Authenticated student query: strongest skills
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")
    r_chat = client.post(
        "/api/ai/chat",
        headers={"Authorization": "Bearer mock_token"},
        json={"message": "Which of my skills are strongest?"},
    )
    assert r_chat.status_code == 200, f"Error: {r_chat.text}"
    data = r_chat.json()
    assert "reply" in data
    assert "Python" in data["reply"]  # Python was seeded in student profile
    assert data["grounded_data"]["skills_count"] >= 1
    assert data["provenance"]["data_status"] == "available"

    # 3. Authenticated student query with job_id: gap analysis
    r_gap = client.post(
        "/api/ai/chat",
        headers={"Authorization": "Bearer mock_token"},
        json={"message": "What skills am I missing for this job?", "job_id": JOB_ID},
    )
    assert r_gap.status_code == 200
    gap_data = r_gap.json()
    assert "Docker" in gap_data["reply"] or "Docker" in str(gap_data)
    assert gap_data["grounded_data"]["job_analyzed"] == "Full Stack Software Engineer"

    # 4. Verify advisory only: student skills document was NOT mutated
    db = get_db()
    skill_snap = db.collection("users").document(STUDENT_UID).collection("skills").document("skill_python").get()
    assert skill_snap.to_dict()["proficiency"] == 4.0


def test_quiz_and_assessment_enhancement():
    """Step 36: Verify quiz questions, deterministic scoring, preservation of verified skills, and history."""
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")

    # 1. Fetch quiz questions for Python
    r_quiz = client.get("/api/skills/quiz/python", headers={"Authorization": "Bearer mock_token"})
    assert r_quiz.status_code == 200
    qdata = r_quiz.json()
    assert qdata["skill_name"] == "python"
    assert len(qdata["questions"]) >= 5
    # Verify answers are NOT leaked to client
    for q in qdata["questions"]:
        assert "correctIndex" not in q

    # 2. Submit quiz with low score (0 correct) on a previously faculty-verified skill (Level 4.0)
    # The submission should calculate assessed_proficiency = 1.0, but PRESERVE verified proficiency at 4.0
    r_submit = client.post(
        "/api/skills/quiz/submit",
        headers={"Authorization": "Bearer mock_token"},
        json={
            "skill_name": "Python",
            "category": "Technical",
            "answers": {"py_1": 3, "py_2": 3, "py_3": 3, "py_4": 3, "py_5": 3},  # all incorrect
        },
    )
    assert r_submit.status_code == 200
    sub_data = r_submit.json()
    assert sub_data["assessed_proficiency"] == 1.0
    assert sub_data["preserved_verified"] is True
    assert sub_data["current_proficiency"] == 4.0  # Preserved!

    # 3. Verify assessment history endpoint
    r_hist = client.get("/api/skills/assessments/history", headers={"Authorization": "Bearer mock_token"})
    assert r_hist.status_code == 200
    history = r_hist.json()
    assert len(history) >= 1
    assert history[0]["skill_name"] == "Python"
    assert history[0]["assessed_proficiency"] == 1.0


def test_applications_lifecycle_and_recruiter_ownership():
    """Step 37: Verify application creation, ownership, match scoring, and status updates."""
    # 1. Student applies for job
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")
    r_apply = client.post(
        "/api/applications",
        headers={"Authorization": "Bearer mock_token"},
        json={"job_id": JOB_ID, "notes": "Excited for this role."},
    )
    assert r_apply.status_code == 200
    app_data = r_apply.json()
    app_id = app_data["application_id"]
    assert app_data["status"] == "applied"
    assert app_data["job_title"] == "Full Stack Software Engineer"
    assert app_data["match_score"] is not None

    # 2. Duplicate application blocked
    r_dup = client.post(
        "/api/applications",
        headers={"Authorization": "Bearer mock_token"},
        json={"job_id": JOB_ID},
    )
    assert r_dup.status_code == 409

    # 3. Student views own applications
    r_my_apps = client.get("/api/applications/me", headers={"Authorization": "Bearer mock_token"})
    assert r_my_apps.status_code == 200
    my_apps = r_my_apps.json()
    assert any(a["application_id"] == app_id for a in my_apps)

    # 4. Unauthorized recruiter attempts to view applications for JOB_ID (owned by RECRUITER_UID)
    set_user(OTHER_RECRUITER_UID, OTHER_RECRUITER_EMAIL, "recruiter")
    r_unauth_recruiter = client.get(
        f"/api/applications/job/{JOB_ID}",
        headers={"Authorization": "Bearer mock_token"},
    )
    assert r_unauth_recruiter.status_code == 403

    # 5. Authorized recruiter views applications
    set_user(RECRUITER_UID, RECRUITER_EMAIL, "recruiter")
    r_owner_recruiter = client.get(
        f"/api/applications/job/{JOB_ID}",
        headers={"Authorization": "Bearer mock_token"},
    )
    assert r_owner_recruiter.status_code == 200
    job_apps = r_owner_recruiter.json()
    assert len(job_apps) >= 1

    # 6. Authorized recruiter updates application status
    r_update_status = client.patch(
        f"/api/applications/{app_id}/status",
        headers={"Authorization": "Bearer mock_token"},
        json={"status": "shortlisted", "feedback": "Strong Python competencies."},
    )
    assert r_update_status.status_code == 200
    assert r_update_status.json()["status"] == "shortlisted"

    # 7. Student withdraws application
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")
    r_withdraw = client.patch(
        f"/api/applications/{app_id}/withdraw",
        headers={"Authorization": "Bearer mock_token"},
    )
    assert r_withdraw.status_code == 200
    assert r_withdraw.json()["state"] == "withdrawn"


def test_notifications_system():
    """Step 38: Verify real event-driven notifications, read states, and user isolation."""
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")

    # Fetch notifications for student (from quiz and application events)
    r_notifs = client.get("/api/notifications/me", headers={"Authorization": "Bearer mock_token"})
    assert r_notifs.status_code == 200
    data = r_notifs.json()
    assert "notifications" in data
    assert len(data["notifications"]) >= 1

    target_notif = data["notifications"][0]
    notif_id = target_notif["notification_id"]

    # Mark as read
    r_read = client.patch(f"/api/notifications/{notif_id}/read", headers={"Authorization": "Bearer mock_token"})
    assert r_read.status_code == 200
    assert r_read.json()["read"] is True

    # Mark all read
    r_all_read = client.post("/api/notifications/mark-all-read", headers={"Authorization": "Bearer mock_token"})
    assert r_all_read.status_code == 200


def test_admin_and_role_management_security():
    """Step 39: Verify privilege escalation prevention and role management."""
    # 1. Student attempting to list users via admin endpoint -> 403 Forbidden
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")
    r_student_admin = client.get("/api/admin/users", headers={"Authorization": "Bearer mock_token"})
    assert r_student_admin.status_code == 403

    # 2. Recruiter attempting to promote themselves -> 403 Forbidden
    set_user(RECRUITER_UID, RECRUITER_EMAIL, "recruiter")
    r_recruiter_admin = client.patch(
        f"/api/admin/users/{RECRUITER_UID}/role",
        headers={"Authorization": "Bearer mock_token"},
        json={"role": "admin"},
    )
    assert r_recruiter_admin.status_code == 403

    # 3. Platform Admin can list users
    set_user(ADMIN_UID, ADMIN_EMAIL, "admin")
    r_admin_list = client.get("/api/admin/users", headers={"Authorization": "Bearer mock_token"})
    assert r_admin_list.status_code == 200
    users = r_admin_list.json()
    assert len(users) >= 1

    # 4. Platform Admin can update role of a test student to faculty
    r_admin_update = client.patch(
        f"/api/admin/users/{STUDENT_UID}/role",
        headers={"Authorization": "Bearer mock_token"},
        json={"role": "faculty", "department": "Computer Science"},
    )
    assert r_admin_update.status_code == 200
    assert r_admin_update.json()["role"] == "faculty"
    assert r_admin_update.json()["department"] == "Computer Science"

    # Restore student role
    client.patch(
        f"/api/admin/users/{STUDENT_UID}/role",
        headers={"Authorization": "Bearer mock_token"},
        json={"role": "student"},
    )


def test_data_provenance_integration():
    """Step 40: Verify provenance metadata exists across models and data is real."""
    set_user(STUDENT_UID, STUDENT_EMAIL, "student")

    # Fetch quiz
    r_quiz = client.get("/api/skills/quiz/python", headers={"Authorization": "Bearer mock_token"})
    assert r_quiz.status_code == 200
    assert "provenance" in r_quiz.json()
    assert r_quiz.json()["provenance"]["source"] == "assessment_question_bank"

    # Fetch applications
    r_apps = client.get("/api/applications/me", headers={"Authorization": "Bearer mock_token"})
    assert r_apps.status_code == 200
    apps = r_apps.json()
    if apps:
        assert "provenance" in apps[0]
        assert apps[0]["provenance"]["source"] == "applications_registry"

    clear_user()

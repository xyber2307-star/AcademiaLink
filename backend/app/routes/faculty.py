"""
Faculty & Mentor Module (Step 33)
Provides secure endpoints for faculty/mentors to:
- View assigned students
- Inspect student skill proficiencies, gaps, learning paths, and evidence
- Review (approve/reject) student evidence with feedback notes
- Submit and track mentoring guidance/feedback
- Access evidence attachment files strictly within assignment boundaries
- Allow students to view their assigned mentor and mentor feedback
"""

from datetime import datetime, timezone
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.firebase import get_db
from app.auth import get_current_user
from app.routes.evidence import BASE_UPLOAD_DIR
from app.routes.skills import serialize_skill
from app.models import (
    AssignedMentorResponse,
    AssignedStudentSummary,
    EvidenceResponse,
    EvidenceReviewActionRequest,
    MentorAssignmentCreate,
    MentorAssignmentResponse,
    MentorFeedbackCreate,
    MentorFeedbackResponse,
    MentorInfo,
    PendingEvidenceItem,
    SkillResponse,
    StudentMentoringDetailResponse,
    UserProfileResponse,
    LearningPathResponse,
)
from app.routes.notifications import create_notification

logger = logging.getLogger("academia.faculty")

router = APIRouter(prefix="/faculty", tags=["Faculty & Mentor"])
student_mentor_router = APIRouter(prefix="/mentor", tags=["Student Mentor"])


# ===================== ROLE DEPENDENCIES & GUARDS =====================

async def require_faculty(
    current_user: UserProfileResponse = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Ensure the authenticated user possesses faculty, mentor, or admin privileges.
    Students and recruiters receive HTTP 403 Forbidden.
    """
    if current_user.role not in ["faculty", "mentor", "admin"]:
        logger.warning(
            "Unauthorized faculty endpoint access attempt by UID=%s with role=%s",
            current_user.uid,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Faculty, mentor, or administrator access required",
        )
    return current_user


async def require_admin(
    current_user: UserProfileResponse = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Ensure the user has administrator privileges for system-wide assignment configuration.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator privileges required to configure mentor assignments",
        )
    return current_user


def is_student_assigned_to_mentor(mentor_uid: str, student_uid: str, db) -> bool:
    """
    Verify if an active assignment exists between mentor_uid and student_uid in Firestore.
    """
    assignments_ref = db.collection("mentor_assignments")
    docs = (
        assignments_ref.where("mentor_uid", "==", mentor_uid)
        .where("student_uid", "==", student_uid)
        .where("status", "==", "active")
        .limit(1)
        .stream()
    )
    for _ in docs:
        return True
    return False


def verify_mentor_access(current_user: UserProfileResponse, student_uid: str, db) -> bool:
    """
    Verify that current_user has permission to access student_uid.
    Admins are granted global access. Mentors must have an active assignment.
    """
    if current_user.role == "admin":
        return True
    if not is_student_assigned_to_mentor(current_user.uid, student_uid, db):
        logger.warning(
            "Access denied: Mentor %s attempted unauthorized access to unassigned student %s",
            current_user.uid,
            student_uid,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Student '{student_uid}' is not assigned to you",
        )
    return True


# ===================== ASSIGNMENT MANAGEMENT (ADMIN / SERVICE) =====================

@router.post("/assignments", response_model=MentorAssignmentResponse, status_code=status.HTTP_201_CREATED, summary="Create or update mentor-student assignment")
async def create_or_update_assignment(
    assignment_in: MentorAssignmentCreate,
    current_user: UserProfileResponse = Depends(require_admin),
):
    """
    Administrative endpoint to assign a student to a faculty/mentor.
    Students attempting to call this are rejected with HTTP 403 Forbidden.
    """
    db = get_db()

    # Verify mentor exists
    mentor_doc = db.collection("users").document(assignment_in.mentor_uid.strip()).get()
    if not mentor_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with UID '{assignment_in.mentor_uid}' does not exist",
        )

    # Verify student exists
    student_doc = db.collection("users").document(assignment_in.student_uid.strip()).get()
    if not student_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with UID '{assignment_in.student_uid}' does not exist",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    assignment_id = f"asgn_{assignment_in.mentor_uid[:8]}_{assignment_in.student_uid[:8]}"
    doc_ref = db.collection("mentor_assignments").document(assignment_id)

    doc_data = {
        "assignment_id": assignment_id,
        "id": assignment_id,
        "mentor_uid": assignment_in.mentor_uid.strip(),
        "student_uid": assignment_in.student_uid.strip(),
        "institution_id": assignment_in.institution_id or "",
        "status": assignment_in.status,
        "updatedAt": now_iso,
    }

    existing = doc_ref.get()
    if not existing.exists:
        doc_data["createdAt"] = now_iso

    doc_ref.set(doc_data, merge=True)
    logger.info(
        "Assignment configured: mentor=%s, student=%s, status=%s",
        assignment_in.mentor_uid,
        assignment_in.student_uid,
        assignment_in.status,
    )
    return MentorAssignmentResponse(**doc_data)


# ===================== FACULTY STUDENT ROSTER & DETAILS =====================

@router.get("/students", response_model=List[AssignedStudentSummary], summary="List assigned students for authenticated faculty")
async def list_assigned_students(
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Return summary list of students actively assigned to the authenticated faculty/mentor.
    """
    db = get_db()
    assigned_students: List[AssignedStudentSummary] = []

    # If admin, fetch all active assignments or allow viewing assigned
    query = db.collection("mentor_assignments").where("status", "==", "active")
    if current_user.role != "admin":
        query = query.where("mentor_uid", "==", current_user.uid)

    assignment_docs = list(query.stream())
    for adoc in assignment_docs:
        adata = adoc.to_dict() or {}
        st_uid = adata.get("student_uid")
        if not st_uid:
            continue

        st_doc = db.collection("users").document(st_uid).get()
        if not st_doc.exists:
            continue

        st_data = st_doc.to_dict() or {}

        # Count skills
        skills_ref = db.collection("users").document(st_uid).collection("skills")
        skill_count = len(list(skills_ref.stream()))

        # Count pending evidence
        evidence_ref = db.collection("users").document(st_uid).collection("evidence")
        pending_count = len([
            e for e in evidence_ref.stream()
            if (e.to_dict() or {}).get("verification_status") == "pending"
        ])

        assigned_students.append(
            AssignedStudentSummary(
                student_uid=st_uid,
                name=st_data.get("name") or "Student",
                email=st_data.get("email") or "",
                avatar=st_data.get("avatar") or "https://i.pravatar.cc/150?img=12",
                targetRole=st_data.get("targetRole") or "Student",
                department=st_data.get("department") or st_data.get("branch") or "",
                institution=st_data.get("institution") or "",
                skill_count=skill_count,
                pending_evidence_count=pending_count,
                assignment_id=adoc.id,
                assignedAt=adata.get("createdAt") or adata.get("updatedAt"),
            )
        )

    return assigned_students


@router.get("/students/{student_uid}", response_model=StudentMentoringDetailResponse, summary="Retrieve detailed student mentoring view")
async def get_assigned_student_detail(
    student_uid: str,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Retrieve comprehensive mentoring dossier for an assigned student:
    - User Profile
    - Verified Skills
    - Learning Paths (Step 30)
    - Evidence Submissions (Step 31)
    - Mentoring Feedback History
    - Job Gap Context (Step 29)
    Strictly verifies assignment; unassigned access returns HTTP 403 Forbidden.
    """
    db = get_db()
    verify_mentor_access(current_user, student_uid, db)

    student_doc = db.collection("users").document(student_uid).get()
    if not student_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with UID '{student_uid}' not found",
        )

    st_dict = student_doc.to_dict() or {}
    st_dict["uid"] = student_uid
    profile = UserProfileResponse(**st_dict)

    # 1. Skills
    skills_docs = db.collection("users").document(student_uid).collection("skills").stream()
    skills: List[SkillResponse] = []
    for sdoc in skills_docs:
        sdata = sdoc.to_dict() or {}
        try:
            skills.append(serialize_skill(sdoc.id, sdata))
        except Exception as e:
            logger.warning("Error serializing skill %s: %s", sdoc.id, e)

    # 2. Learning Paths
    lpaths_docs = db.collection("users").document(student_uid).collection("learning_paths").stream()
    learning_paths: List[LearningPathResponse] = []
    for lpdoc in lpaths_docs:
        lpdata = lpdoc.to_dict() or {}
        lpdata["path_id"] = lpdoc.id
        try:
            learning_paths.append(LearningPathResponse(**lpdata))
        except Exception:
            pass

    # 3. Evidence
    evidence_docs = db.collection("users").document(student_uid).collection("evidence").stream()
    evidence: List[EvidenceResponse] = []
    for edoc in evidence_docs:
        edata = edoc.to_dict() or {}
        edata["evidence_id"] = edoc.id
        edata["id"] = edoc.id
        edata["user_id"] = student_uid
        try:
            evidence.append(EvidenceResponse(**edata))
        except Exception:
            pass

    # 4. Feedback
    fb_docs = db.collection("users").document(student_uid).collection("mentor_feedback").stream()
    feedback: List[MentorFeedbackResponse] = []
    for fdoc in fb_docs:
        fdata = fdoc.to_dict() or {}
        fdata["feedback_id"] = fdoc.id
        fdata["id"] = fdoc.id
        fdata["student_uid"] = student_uid
        try:
            feedback.append(MentorFeedbackResponse(**fdata))
        except Exception:
            pass

    feedback.sort(key=lambda x: x.createdAt or "", reverse=True)

    # 5. Extract skill gaps from active learning path if available
    skill_gaps: List[Dict[str, Any]] = []
    active_paths = [lp for lp in learning_paths if lp.status == "active"]
    if active_paths:
        for sk in active_paths[0].skills:
            if sk.gap > 0:
                skill_gaps.append({
                    "skill": sk.skill_name,
                    "required_proficiency": sk.required_proficiency,
                    "student_proficiency": sk.current_proficiency,
                    "gap": sk.gap,
                    "priority": sk.priority,
                    "target_job": active_paths[0].target_job_title,
                })

    return StudentMentoringDetailResponse(
        student_uid=student_uid,
        profile=profile,
        skills=skills,
        learning_paths=learning_paths,
        evidence=evidence,
        feedback=feedback,
        skill_gaps=skill_gaps,
    )


# ===================== EVIDENCE REVIEW ENDPOINTS =====================

@router.get("/evidence/pending", response_model=List[PendingEvidenceItem], summary="List pending evidence awaiting review from assigned students")
async def list_pending_evidence(
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Return all evidence items with verification_status == 'pending' submitted by
    students assigned to the authenticated faculty/mentor.
    """
    db = get_db()
    pending_items: List[PendingEvidenceItem] = []

    # Get assigned students
    query = db.collection("mentor_assignments").where("status", "==", "active")
    if current_user.role != "admin":
        query = query.where("mentor_uid", "==", current_user.uid)

    assignment_docs = list(query.stream())
    for adoc in assignment_docs:
        adata = adoc.to_dict() or {}
        st_uid = adata.get("student_uid")
        if not st_uid:
            continue

        st_doc = db.collection("users").document(st_uid).get()
        st_name = "Student"
        st_email = ""
        if st_doc.exists:
            st_info = st_doc.to_dict() or {}
            st_name = st_info.get("name") or "Student"
            st_email = st_info.get("email") or ""

        ev_docs = (
            db.collection("users")
            .document(st_uid)
            .collection("evidence")
            .where("verification_status", "==", "pending")
            .stream()
        )

        for edoc in ev_docs:
            edata = edoc.to_dict() or {}
            edata["evidence_id"] = edoc.id
            edata["id"] = edoc.id
            edata["user_id"] = st_uid
            edata["student_name"] = st_name
            edata["student_email"] = st_email
            try:
                pending_items.append(PendingEvidenceItem(**edata))
            except Exception:
                pass

    return pending_items


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse, summary="Get evidence details with assignment verification")
async def get_evidence_detail(
    evidence_id: str,
    student_uid: Optional[str] = Query(None, description="Student UID owning the evidence"),
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Retrieve evidence document if the owning student is assigned to the authenticated mentor.
    """
    db = get_db()

    resolved_student_uid = student_uid
    if not resolved_student_uid:
        # Search among assigned students
        query = db.collection("mentor_assignments").where("status", "==", "active")
        if current_user.role != "admin":
            query = query.where("mentor_uid", "==", current_user.uid)

        for adoc in query.stream():
            candidate_uid = (adoc.to_dict() or {}).get("student_uid")
            if not candidate_uid:
                continue
            ev_check = (
                db.collection("users")
                .document(candidate_uid)
                .collection("evidence")
                .document(evidence_id.strip())
                .get()
            )
            if ev_check.exists:
                resolved_student_uid = candidate_uid
                break

    if not resolved_student_uid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' not found among assigned students",
        )

    verify_mentor_access(current_user, resolved_student_uid, db)

    doc_ref = (
        db.collection("users")
        .document(resolved_student_uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' not found",
        )

    data = doc.to_dict() or {}
    data["evidence_id"] = doc.id
    data["id"] = doc.id
    data["user_id"] = resolved_student_uid
    return EvidenceResponse(**data)


@router.patch("/evidence/{evidence_id}/review", response_model=EvidenceResponse, summary="Approve or reject student evidence with notes")
async def review_evidence(
    evidence_id: str,
    review_in: EvidenceReviewActionRequest,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Allow authorized faculty to approve or reject evidence submitted by an assigned student.
    Enforces:
    1. Faculty authentication and role.
    2. Existence of evidence.
    3. Active mentor-student assignment.
    4. Valid action (approved / rejected).
    5. Server-stamped reviewer_id and reviewedAt timestamp.
    6. Skill integrity: does NOT arbitrarily change skill proficiency levels.
    """
    db = get_db()
    if review_in.verification_status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="verification_status must be either 'approved' or 'rejected'",
        )

    # Resolve student UID
    resolved_student_uid = review_in.student_uid
    if not resolved_student_uid:
        query = db.collection("mentor_assignments").where("status", "==", "active")
        if current_user.role != "admin":
            query = query.where("mentor_uid", "==", current_user.uid)

        for adoc in query.stream():
            candidate_uid = (adoc.to_dict() or {}).get("student_uid")
            if not candidate_uid:
                continue
            ev_check = (
                db.collection("users")
                .document(candidate_uid)
                .collection("evidence")
                .document(evidence_id.strip())
                .get()
            )
            if ev_check.exists:
                resolved_student_uid = candidate_uid
                break

    if not resolved_student_uid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{evidence_id}' not found among assigned students",
        )

    verify_mentor_access(current_user, resolved_student_uid, db)

    doc_ref = (
        db.collection("users")
        .document(resolved_student_uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{evidence_id}' does not exist",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    review_updates = {
        "verification_status": review_in.verification_status,
        "verification_notes": (review_in.verification_notes or "").strip(),
        "reviewer_id": current_user.uid,
        "reviewedAt": now_iso,
        "updatedAt": now_iso,
    }

    doc_ref.update(review_updates)
    data = doc.to_dict() or {}
    data.update(review_updates)
    data["evidence_id"] = doc.id
    data["id"] = doc.id
    data["user_id"] = resolved_student_uid

    logger.info(
        "Faculty %s reviewed evidence %s for student %s: status=%s",
        current_user.uid,
        evidence_id,
        resolved_student_uid,
        review_in.verification_status,
    )

    create_notification(
        db,
        resolved_student_uid,
        "evidence_reviewed",
        f"Evidence {review_in.verification_status.capitalize()}: {data.get('title', 'Portfolio Item')}",
        f"Faculty {current_user.name or 'Mentor'} {review_in.verification_status} your evidence submission.",
        related_id=evidence_id,
    )

    return EvidenceResponse(**data)


@router.get("/students/{student_uid}/evidence/{evidence_id}/file", summary="Stream evidence attachment file to assigned faculty")
async def get_student_evidence_file(
    student_uid: str,
    evidence_id: str,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Stream private evidence attachment to assigned faculty only.
    Rejects unassigned faculty with HTTP 403 Forbidden.
    """
    db = get_db()
    verify_mentor_access(current_user, student_uid, db)

    doc_ref = (
        db.collection("users")
        .document(student_uid)
        .collection("evidence")
        .document(evidence_id.strip())
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' not found",
        )

    data = doc.to_dict() or {}
    rel_path = data.get("file_path")
    if not rel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file attached to this evidence item",
        )

    safe_filename = os.path.basename(rel_path)
    file_full_path = os.path.join(BASE_UPLOAD_DIR, student_uid, safe_filename)

    if not os.path.exists(file_full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced evidence file could not be found on server",
        )

    return FileResponse(file_full_path, filename=safe_filename)


# ===================== MENTOR FEEDBACK ENDPOINTS =====================

@router.post("/students/{student_uid}/feedback", response_model=MentorFeedbackResponse, status_code=status.HTTP_201_CREATED, summary="Create mentor feedback for assigned student")
async def create_mentor_feedback(
    student_uid: str,
    feedback_in: MentorFeedbackCreate,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Allow faculty/mentor to create guidance/feedback for an assigned student.
    Unassigned faculty attempts return HTTP 403 Forbidden.
    """
    db = get_db()
    verify_mentor_access(current_user, student_uid, db)

    # Verify student exists
    student_doc = db.collection("users").document(student_uid).get()
    if not student_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_uid}' does not exist",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    fb_id = f"fb_{uuid.uuid4().hex[:10]}"
    doc_ref = (
        db.collection("users")
        .document(student_uid)
        .collection("mentor_feedback")
        .document(fb_id)
    )

    doc_data = {
        "feedback_id": fb_id,
        "id": fb_id,
        "student_uid": student_uid,
        "mentor_uid": current_user.uid,
        "mentor_name": current_user.name or "Faculty Mentor",
        "message": feedback_in.message.strip(),
        "related_skill_id": feedback_in.related_skill_id,
        "related_learning_path_id": feedback_in.related_learning_path_id,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }

    doc_ref.set(doc_data)
    logger.info("Faculty %s provided feedback %s to student %s", current_user.uid, fb_id, student_uid)

    create_notification(
        db,
        student_uid,
        "mentor_feedback",
        f"New Mentor Feedback from {current_user.name or 'Faculty Mentor'}",
        feedback_in.message.strip()[:150],
        related_id=fb_id,
    )

    return MentorFeedbackResponse(**doc_data)


@router.get("/students/{student_uid}/feedback", response_model=List[MentorFeedbackResponse], summary="List feedback history for assigned student")
async def get_student_feedback_history(
    student_uid: str,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """
    Retrieve all mentor feedback for an assigned student.
    """
    db = get_db()
    verify_mentor_access(current_user, student_uid, db)

    fb_docs = (
        db.collection("users")
        .document(student_uid)
        .collection("mentor_feedback")
        .stream()
    )

    feedback: List[MentorFeedbackResponse] = []
    for doc in fb_docs:
        fdata = doc.to_dict() or {}
        fdata["feedback_id"] = doc.id
        fdata["id"] = doc.id
        fdata["student_uid"] = student_uid
        try:
            feedback.append(MentorFeedbackResponse(**fdata))
        except Exception:
            pass

    feedback.sort(key=lambda x: x.createdAt or "", reverse=True)
    return feedback


# ===================== STUDENT-FACING MENTOR APIS =====================

@student_mentor_router.get("/me", response_model=AssignedMentorResponse, summary="Get authenticated student's assigned mentor")
async def get_my_assigned_mentor(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Return the authenticated student's assigned mentor if an active assignment exists.
    If no mentor is assigned, returns assigned=False with mentor=None. Zero fake mentors.
    """
    db = get_db()
    assignments = (
        db.collection("mentor_assignments")
        .where("student_uid", "==", current_user.uid)
        .where("status", "==", "active")
        .limit(1)
        .stream()
    )

    assignment_doc = None
    for adoc in assignments:
        assignment_doc = adoc
        break

    if not assignment_doc:
        return AssignedMentorResponse(assigned=False, mentor=None)

    adata = assignment_doc.to_dict() or {}
    mentor_uid = adata.get("mentor_uid")
    if not mentor_uid:
        return AssignedMentorResponse(assigned=False, mentor=None)

    mentor_doc = db.collection("users").document(mentor_uid).get()
    if not mentor_doc.exists:
        return AssignedMentorResponse(assigned=False, mentor=None)

    mdata = mentor_doc.to_dict() or {}
    mentor_info = MentorInfo(
        uid=mentor_uid,
        name=mdata.get("name") or "Faculty Mentor",
        email=mdata.get("email") or "",
        avatar=mdata.get("avatar") or "https://i.pravatar.cc/150?img=60",
        department=mdata.get("department") or "",
        institution=mdata.get("institution") or "",
        role=mdata.get("role") or "faculty",
    )

    return AssignedMentorResponse(assigned=True, mentor=mentor_info)


@student_mentor_router.get("/me/feedback", response_model=List[MentorFeedbackResponse], summary="Get authenticated student's mentor feedback")
async def get_my_mentor_feedback(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Retrieve feedback and guidance given to the authenticated student by their mentor.
    """
    db = get_db()
    fb_docs = (
        db.collection("users")
        .document(current_user.uid)
        .collection("mentor_feedback")
        .stream()
    )

    feedback: List[MentorFeedbackResponse] = []
    for doc in fb_docs:
        fdata = doc.to_dict() or {}
        fdata["feedback_id"] = doc.id
        fdata["id"] = doc.id
        fdata["student_uid"] = current_user.uid
        try:
            feedback.append(MentorFeedbackResponse(**fdata))
        except Exception:
            pass

    feedback.sort(key=lambda x: x.createdAt or "", reverse=True)
    return feedback

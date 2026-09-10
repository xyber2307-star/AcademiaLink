from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.firebase import get_db
from app.models import (
    LearningPathCreate,
    LearningPathResponse,
    LearningPathSkillItem,
    LearningPathSkillUpdate,
    LearningPathStatusUpdate,
    UserProfileResponse,
)
from app.routes.matching import compute_weighted_job_match

logger = logging.getLogger("academialink.learning_paths")

router = APIRouter(prefix="/learning-paths", tags=["Learning Paths & Recommendations"])


def calculate_learning_priority(
    gap: float,
    weight: float,
    is_missing: bool,
) -> tuple[float, str, str]:
    """
    Deterministic Learning Priority Algorithm (STEP 30):
      gap = max(required_proficiency - current_proficiency, 0)
      missing_multiplier = 1.25 if is_missing else 1.0
      priority_score = round(gap * weight * missing_multiplier, 2)

    Classification:
      priority_score >= 4.0 -> High
      2.0 <= priority_score < 4.0 -> Medium
      priority_score < 2.0 -> Low
    """
    missing_multiplier = 1.25 if is_missing else 1.0
    priority_score = round(gap * weight * missing_multiplier, 2)

    if priority_score >= 4.0:
        priority = "High"
    elif priority_score >= 2.0:
        priority = "Medium"
    else:
        priority = "Low"

    if is_missing:
        reason = (
            f"Missing skill with gap of {gap:.1f} and high job importance (weight {weight:.1f}x). "
            f"Building this competency is vital for role eligibility."
        )
    else:
        reason = (
            f"Partial proficiency gap of {gap:.1f} against required level with job weight of {weight:.1f}x. "
            f"Advancing this skill increases candidate competitiveness."
        )

    return priority_score, priority, reason


@router.get("/me", response_model=List[LearningPathResponse], summary="List authenticated student's learning paths")
async def list_my_learning_paths(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve all learning paths from users/{uid}/learning_paths."""
    try:
        db = get_db()
        paths_ref = db.collection("users").document(current_user.uid).collection("learning_paths")
        docs = paths_ref.stream()

        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["path_id"] = doc.id
            results.append(LearningPathResponse(**data))
        return results
    except Exception as e:
        logger.error("Error retrieving learning paths for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning paths: {str(e)}",
        )


@router.get("/me/{path_id}", response_model=LearningPathResponse, summary="Get details for a specific learning path")
async def get_my_learning_path(
    path_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve one learning path belonging to the authenticated student."""
    try:
        db = get_db()
        doc_ref = (
            db.collection("users")
            .document(current_user.uid)
            .collection("learning_paths")
            .document(path_id)
        )
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID '{path_id}' not found for current user",
            )
        data = doc.to_dict() or {}
        data["path_id"] = doc.id
        return LearningPathResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving learning path %s for user %s: %s", path_id, current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("", response_model=LearningPathResponse, status_code=status.HTTP_201_CREATED, summary="Create a personalized learning path for a target job")
async def create_learning_path(
    path_in: LearningPathCreate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Generate a personalized, explainable learning path based on the student's real skills,
    the target job's requirements, and deterministic priority calculations.
    """
    db = get_db()
    job_id = path_in.job_id.strip()

    # 1. Fetch target job
    job_doc = db.collection("jobs").document(job_id).get()
    if not job_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target job with ID '{job_id}' not found",
        )
    job_data = job_doc.to_dict() or {}
    job_title = job_data.get("title", "Target Opportunity")
    company = job_data.get("company", "Company")
    required_skills = job_data.get("required_skills") or job_data.get("requiredSkills") or []

    # 2. Fetch student's current skills from users/{uid}/skills
    skills_docs = db.collection("users").document(current_user.uid).collection("skills").stream()
    student_skills = {}
    for sdoc in skills_docs:
        sdata = sdoc.to_dict() or {}
        sname = sdata.get("name")
        if sname:
            student_skills[sname] = float(sdata.get("proficiency", sdata.get("score", 3)))

    # 3. Compute skill gap analysis from Step 29
    overall_score, matched, partial, missing, prioritized_gaps, explanation = compute_weighted_job_match(
        student_skills, required_skills
    )

    # 4. Generate structured learning path skills
    learning_skills: List[LearningPathSkillItem] = []
    gaps_to_process = partial + missing

    for gap_item in gaps_to_process:
        is_missing = gap_item.gap_category == "missing"
        p_score, priority, reason = calculate_learning_priority(
            gap_item.gap_amount, gap_item.weight, is_missing
        )
        safe_skill_id = f"skill_{gap_item.skill.lower().replace(' ', '_')}"
        learning_skills.append(
            LearningPathSkillItem(
                skill_id=safe_skill_id,
                skill_name=gap_item.skill,
                current_proficiency=gap_item.current_proficiency,
                required_proficiency=gap_item.required_proficiency,
                gap=gap_item.gap_amount,
                job_weight=gap_item.weight,
                priority=priority,
                priority_score=p_score,
                reason=reason,
                status="not_started",
            )
        )

    # Sort learning skills by deterministic priority (-priority_score, -gap, -job_weight)
    learning_skills.sort(key=lambda s: (-s.priority_score, -s.gap, -s.job_weight))

    now_iso = datetime.now(timezone.utc).isoformat()
    paths_ref = db.collection("users").document(current_user.uid).collection("learning_paths")
    new_doc_ref = paths_ref.document()

    path_data = {
        "path_id": new_doc_ref.id,
        "user_id": current_user.uid,
        "target_job_id": job_id,
        "target_job_title": job_title,
        "target_company": company,
        "skills": [s.model_dump() for s in learning_skills],
        "overall_match_before": overall_score,
        "overall_match_after": 100.0,
        "status": "active",
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }

    new_doc_ref.set(path_data)
    logger.info("Generated learning path %s for user %s targeting job %s", new_doc_ref.id, current_user.uid, job_id)

    return LearningPathResponse(**path_data)


@router.patch("/me/{path_id}/skills/{skill_id}", response_model=LearningPathResponse, summary="Update progress status of a skill within a learning path")
async def update_learning_path_skill_progress(
    path_id: str,
    skill_id: str,
    update_in: LearningPathSkillUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Update the student's personal study progress for a skill in their learning path.
    DATA INTEGRITY: This updates syllabus tracking within the learning path ONLY.
    It DOES NOT modify or fake official proficiency in users/{uid}/skills.
    """
    try:
        db = get_db()
        doc_ref = (
            db.collection("users")
            .document(current_user.uid)
            .collection("learning_paths")
            .document(path_id)
        )
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID '{path_id}' not found for current user",
            )

        data = doc.to_dict() or {}
        skills_list = data.get("skills", [])

        found = False
        target_id_lower = skill_id.strip().lower()
        for s in skills_list:
            if (
                s.get("skill_id", "").lower() == target_id_lower
                or s.get("skill_name", "").lower() == target_id_lower
            ):
                s["status"] = update_in.status
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill '{skill_id}' not found in learning path '{path_id}'",
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        data["updatedAt"] = now_iso
        doc_ref.set(data)

        data["path_id"] = doc.id
        return LearningPathResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating skill progress in learning path %s: %s", path_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating skill progress: {str(e)}",
        )


@router.patch("/me/{path_id}/status", response_model=LearningPathResponse, summary="Update learning path lifecycle status")
async def update_learning_path_status(
    path_id: str,
    update_in: LearningPathStatusUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Update learning path lifecycle status: active, completed, or archived."""
    try:
        db = get_db()
        doc_ref = (
            db.collection("users")
            .document(current_user.uid)
            .collection("learning_paths")
            .document(path_id)
        )
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID '{path_id}' not found for current user",
            )

        data = doc.to_dict() or {}
        now_iso = datetime.now(timezone.utc).isoformat()
        data["status"] = update_in.status
        data["updatedAt"] = now_iso
        doc_ref.set(data)

        data["path_id"] = doc.id
        return LearningPathResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating status for learning path %s: %s", path_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

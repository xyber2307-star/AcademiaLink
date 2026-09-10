"""
Institution Analytics Module (Step 34)
Provides deterministic, real-time analytics for institution administrators:
- Student competency overviews and active participation
- Institution-wide skill distributions and proficiency levels (1-5 scale)
- Curricular skill gaps and learning path progress
- Portfolio evidence verification metrics
- Mentorship and faculty guidance activity
- Industry alignment against published opportunity requirements
Strictly calculates metrics from genuine Firestore documents without fake or hardcoded data.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_institution
from app.firebase import get_db
from app.models import (
    EvidenceAnalyticsMetrics,
    InstitutionAnalyticsResponse,
    LearningAnalyticsMetrics,
    MentorshipAnalyticsMetrics,
    RecruitmentAnalyticsMetrics,
    SkillAnalyticsMetrics,
    SkillDistributionItem,
    StudentOverviewMetrics,
    UserProfileResponse,
)
from app.routes.matching import compute_weighted_job_match

logger = logging.getLogger("academia.institution")

router = APIRouter(prefix="/institution", tags=["Institution Analytics"])

PROFICIENCY_LABEL_MAP = {
    1: "Beginner",
    2: "Basic",
    3: "Intermediate",
    4: "Advanced",
    5: "Expert",
}


@router.get("/analytics", response_model=InstitutionAnalyticsResponse, summary="Retrieve real-time institution analytics")
async def get_institution_analytics(
    institution_id: Optional[str] = Query(None, description="Institution identifier (must match admin scope)"),
    current_user: UserProfileResponse = Depends(require_institution),
):
    """
    Retrieve comprehensive analytics aggregated purely from real Firestore records for the admin's institution.
    Enforces:
    1. Authentication via Firebase Bearer token.
    2. Server-side institution role verification.
    3. Multi-tenant scoping: an institution admin cannot request another institution's data (HTTP 403).
    4. Deterministic computation with zero fake data.
    """
    db = get_db()

    # Determine and validate institution scope
    user_inst_id = (current_user.institution_id or current_user.institution or "").strip()
    target_inst_id = user_inst_id

    if current_user.role == "institution":
        if institution_id:
            req_inst = institution_id.strip()
            # If admin has an assigned institution, query must match it
            if user_inst_id and req_inst.lower() != user_inst_id.lower():
                logger.warning(
                    "Institution admin %s attempted unauthorized cross-institution query for %s",
                    current_user.uid,
                    req_inst,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You cannot request analytics for another institution",
                )
            target_inst_id = req_inst
        elif not target_inst_id:
            target_inst_id = "default_institution"
    elif current_user.role == "admin":
        if institution_id:
            target_inst_id = institution_id.strip()
        elif not target_inst_id:
            target_inst_id = "all"

    # 1. Fetch Students matching the institution scope
    students_query = db.collection("users").where("role", "==", "student")
    all_students_stream = list(students_query.stream())

    target_student_docs = []
    for sdoc in all_students_stream:
        sdata = sdoc.to_dict() or {}
        st_inst_id = (sdata.get("institution_id") or "").strip()
        st_inst_name = (sdata.get("institution") or "").strip()

        if target_inst_id == "all":
            target_student_docs.append((sdoc.id, sdata))
        else:
            # Match either institution_id or institution name
            if (
                (st_inst_id and st_inst_id.lower() == target_inst_id.lower())
                or (st_inst_name and st_inst_name.lower() == target_inst_id.lower())
            ):
                target_student_docs.append((sdoc.id, sdata))

    total_students = len(target_student_docs)
    student_uids = [sid for sid, _ in target_student_docs]

    # Initialize aggregators
    students_with_skills = 0
    students_with_learning_paths = 0
    active_students = 0

    total_skills_count = 0
    skill_occurrences: Dict[str, List[float]] = defaultdict(list)
    skill_category_counter = Counter()
    proficiency_counter = Counter({"Beginner": 0, "Basic": 0, "Intermediate": 0, "Advanced": 0, "Expert": 0})
    skill_categories: Dict[str, str] = {}

    total_learning_paths = 0
    paths_by_status = Counter({"active": 0, "completed": 0, "archived": 0})
    skills_by_status = Counter({"not_started": 0, "in_progress": 0, "completed": 0})
    priority_skills_counter = Counter()
    skill_gaps_counter: Dict[str, List[float]] = defaultdict(list)

    total_evidence_count = 0
    evidence_status_counter = Counter({"pending": 0, "approved": 0, "rejected": 0})
    evidence_type_counter = Counter()
    total_feedback_count = 0

    student_skills_map: Dict[str, List[Dict[str, Any]]] = {}

    # 2. Aggregate across individual student subcollections
    for sid, sdata in target_student_docs:
        has_skill = False
        has_path = False
        has_activity = (sdata.get("profileCompletion") or 0) > 0

        # A. Skills subcollection
        sk_docs = list(db.collection("users").document(sid).collection("skills").stream())
        if sk_docs:
            has_skill = True
            students_with_skills += 1
            total_skills_count += len(sk_docs)
            student_skills_map[sid] = []

            for sk in sk_docs:
                sk_data = sk.to_dict() or {}
                name = (sk_data.get("name") or "Skill").strip()
                raw_prof = sk_data.get("proficiency", 1)
                try:
                    prof_int = max(1, min(5, int(raw_prof)))
                except (ValueError, TypeError):
                    prof_int = 1

                skill_occurrences[name].append(float(prof_int))
                cat = sk_data.get("category") or "Technical"
                skill_category_counter[cat] += 1
                skill_categories[name] = cat
                prof_label = PROFICIENCY_LABEL_MAP.get(prof_int, "Intermediate")
                proficiency_counter[prof_label] += 1

                student_skills_map[sid].append({"name": name, "proficiency": float(prof_int)})

        # B. Learning Paths subcollection
        lp_docs = list(db.collection("users").document(sid).collection("learning_paths").stream())
        if lp_docs:
            has_path = True
            students_with_learning_paths += 1
            total_learning_paths += len(lp_docs)

            for lp in lp_docs:
                lp_data = lp.to_dict() or {}
                status_val = lp_data.get("status", "active")
                paths_by_status[status_val] += 1

                skills_list = lp_data.get("skills") or []
                for s_item in skills_list:
                    if isinstance(s_item, dict):
                        st_val = s_item.get("status", "not_started")
                        skills_by_status[st_val] += 1
                        s_name = s_item.get("skill_name") or s_item.get("name") or ""
                        if s_name:
                            prio = s_item.get("priority", "Medium")
                            if prio in ["High", "Medium"]:
                                priority_skills_counter[s_name] += 1
                            gap_val = float(s_item.get("gap") or 0.0)
                            if gap_val > 0:
                                skill_gaps_counter[s_name].append(gap_val)

        # C. Evidence subcollection
        ev_docs = list(db.collection("users").document(sid).collection("evidence").stream())
        if ev_docs:
            total_evidence_count += len(ev_docs)
            for ev in ev_docs:
                ev_data = ev.to_dict() or {}
                ev_st = ev_data.get("verification_status", "pending")
                evidence_status_counter[ev_st] += 1
                ev_type = ev_data.get("type", "project")
                evidence_type_counter[ev_type] += 1

        # D. Feedback subcollection
        fb_docs = list(db.collection("users").document(sid).collection("mentor_feedback").stream())
        total_feedback_count += len(fb_docs)

        if has_skill or has_path or has_activity or ev_docs or fb_docs:
            active_students += 1

    # 3. Mentorship Analytics
    # Query mentor_assignments related to these students or this institution
    mentor_query = db.collection("mentor_assignments")
    all_asgns = list(mentor_query.stream())

    matching_asgns = []
    for adoc in all_asgns:
        adata = adoc.to_dict() or {}
        st_uid = adata.get("student_uid")
        asgn_inst = adata.get("institution_id")
        if (st_uid in student_uids) or (target_inst_id != "all" and asgn_inst == target_inst_id):
            matching_asgns.append(adata)

    total_mentor_assignments = len(matching_asgns)
    active_mentor_assignments = sum(1 for a in matching_asgns if a.get("status") == "active")
    assigned_students_set = {a.get("student_uid") for a in matching_asgns if a.get("status") == "active" and a.get("student_uid")}
    assigned_students_count = len(assigned_students_set)

    # Pending evidence reviews across assigned students
    pending_reviews_count = evidence_status_counter.get("pending", 0)

    # 4. Recruitment & Market Demand Analytics
    # Query published jobs
    jobs_docs = list(db.collection("jobs").where("status", "==", "published").stream())
    # Backwards compatibility: include legacy jobs without status
    if not jobs_docs:
        all_jobs = list(db.collection("jobs").stream())
        jobs_docs = [j for j in all_jobs if (j.to_dict() or {}).get("status") in ["published", None]]

    relevant_jobs_count = len(jobs_docs)
    job_skill_counter = Counter()
    match_scores: List[float] = []

    for jdoc in jobs_docs:
        jdata = jdoc.to_dict() or {}
        req_skills = jdata.get("required_skills") or []
        for rsk in req_skills:
            if isinstance(rsk, dict):
                rname = (rsk.get("name") or "").strip()
                if rname:
                    job_skill_counter[rname] += 1

        # Calculate sample match scores for institutional students against published jobs
        for sid, sk_list in student_skills_map.items():
            if sk_list and req_skills:
                try:
                    match_res = compute_weighted_job_match(sk_list, req_skills)
                    match_scores.append(float(match_res.get("overall_score", 0.0)))
                except Exception:
                    pass

    avg_match_score = round(sum(match_scores) / len(match_scores), 1) if match_scores else 0.0

    # Top demand skills
    top_demand_skills = [
        {"skill": skill_name, "postings_count": count}
        for skill_name, count in job_skill_counter.most_common(5)
    ]

    # Most common skills
    most_common_skills: List[SkillDistributionItem] = []
    for s_name, prof_list in sorted(skill_occurrences.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        avg_prof = round(sum(prof_list) / len(prof_list), 1) if prof_list else 1.0
        most_common_skills.append(
            SkillDistributionItem(
                name=s_name,
                count=len(prof_list),
                average_proficiency=avg_prof,
                category=skill_categories.get(s_name, "Technical"),
            )
        )

    # Common skill gaps
    common_skill_gaps = [
        {"skill": gap_name, "affected_students": len(gaps), "average_gap": round(sum(gaps) / len(gaps), 1)}
        for gap_name, gaps in sorted(skill_gaps_counter.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    ]

    # Common priority skills
    common_priority_skills = [
        {"skill": p_name, "priority_count": p_count}
        for p_name, p_count in priority_skills_counter.most_common(5)
    ]

    # Resolve institution name
    inst_display_name = current_user.institution or (target_inst_id.replace("_", " ").title() if target_inst_id != "all" else "All Institutions")
    for _, sdata in target_student_docs:
        if sdata.get("institution"):
            inst_display_name = sdata.get("institution")
            break

    now_iso = datetime.now(timezone.utc).isoformat()

    return InstitutionAnalyticsResponse(
        institution_id=target_inst_id,
        institution_name=inst_display_name,
        generated_at=now_iso,
        student_overview=StudentOverviewMetrics(
            total_students=total_students,
            active_students=active_students,
            students_with_skills=students_with_skills,
            students_with_learning_paths=students_with_learning_paths,
        ),
        skill_analytics=SkillAnalyticsMetrics(
            total_skills_recorded=total_skills_count,
            most_common_skills=most_common_skills,
            proficiency_distribution=dict(proficiency_counter),
            category_distribution=dict(skill_category_counter),
            common_skill_gaps=common_skill_gaps,
        ),
        learning_analytics=LearningAnalyticsMetrics(
            total_learning_paths=total_learning_paths,
            paths_by_status=dict(paths_by_status),
            skills_by_status=dict(skills_by_status),
            common_priority_skills=common_priority_skills,
        ),
        evidence_analytics=EvidenceAnalyticsMetrics(
            total_evidence_submissions=total_evidence_count,
            evidence_by_status=dict(evidence_status_counter),
            evidence_by_type=dict(evidence_type_counter),
        ),
        mentorship_analytics=MentorshipAnalyticsMetrics(
            total_mentor_assignments=total_mentor_assignments,
            active_mentor_assignments=active_mentor_assignments,
            assigned_students_count=assigned_students_count,
            feedback_activity_count=total_feedback_count,
            pending_evidence_reviews=pending_reviews_count,
        ),
        recruitment_analytics=RecruitmentAnalyticsMetrics(
            relevant_jobs_count=relevant_jobs_count,
            average_match_score=avg_match_score,
            top_demand_skills=top_demand_skills,
        ),
    )

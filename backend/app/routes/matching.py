import logging
import math
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_faculty, require_student
from app.firebase import get_db
from app.models import (
    CourseCreate,
    CourseResponse,
    JobMatchAnalysisResponse,
    JobMatchResponse,
    JobResponse,
    MatchedSkillItem,
    RoleBenchmarkResponse,
    SkillGapAnalysisItem,
    SkillGapItem,
    UserProfileResponse,
)

logger = logging.getLogger("academialink.matching")

router = APIRouter(prefix="/matching", tags=["Skill Gap Analysis & Matching"])

# Standard Target Role Benchmarks (0-100 scale)
ROLE_BENCHMARKS = {
    "Full-Stack Developer": {
        "React": 80,
        "JavaScript": 85,
        "TypeScript": 80,
        "Node.js": 80,
        "System Design": 75,
        "SQL & Databases": 78,
        "Data Structures": 85,
        "Cloud (AWS)": 70,
        "Docker & CI/CD": 70,
        "Git": 75,
    },
    "Frontend Engineer": {
        "React": 85,
        "JavaScript": 90,
        "TypeScript": 85,
        "HTML/CSS": 90,
        "Testing (Jest)": 75,
        "Performance Optimization": 75,
        "Git": 75,
    },
    "Backend Engineer": {
        "Python": 80,
        "Node.js": 80,
        "SQL & Databases": 85,
        "System Design": 80,
        "Docker & CI/CD": 75,
        "API Design": 85,
        "Data Structures": 85,
    },
    "DevOps Engineer": {
        "Docker & CI/CD": 85,
        "Cloud (AWS)": 85,
        "Linux": 85,
        "Kubernetes": 75,
        "Terraform": 70,
        "Python": 70,
    },
    "Data Scientist": {
        "Python": 90,
        "Machine Learning": 85,
        "SQL & Databases": 80,
        "Data Structures": 80,
        "Statistics": 85,
        "Data Visualization": 75,
    },
}

RECOMMENDED_COURSES = {
    "System Design": "Grokking System Design",
    "Docker & CI/CD": "DevOps Bootcamp",
    "Testing (Jest)": "Testing JavaScript",
    "Cloud (AWS)": "AWS Solutions Architect",
    "TypeScript": "Total TypeScript",
    "Node.js": "Node.js Advanced Concepts",
    "Data Structures": "DSA Masterclass",
    "SQL & Databases": "SQL for Developers",
    "React": "Epic React Pro",
    "JavaScript": "Modern JavaScript Deep Dive",
    "Python": "Python Backend Mastery",
    "Machine Learning": "Machine Learning Specialization",
}


def compute_weighted_job_match(
    student_skills: Dict[str, float],
    required_skills: List[dict],
) -> tuple[float, List[SkillGapAnalysisItem], List[SkillGapAnalysisItem], List[SkillGapAnalysisItem], List[SkillGapAnalysisItem], str]:
    """
    Deterministic Weighted Matching Algorithm (STEP 29):
    For each required skill:
      skill_score = min(student_proficiency / required_proficiency, 1.0)
      weighted_score = skill_score * weight
      overall_score = (sum(weighted_scores) / sum(weights)) * 100

    If student does not possess the skill, student_proficiency = 0.0.

    Gap Categories:
      - matched: student_proficiency >= required_proficiency (gap_amount = 0.0)
      - partial: 0 < student_proficiency < required_proficiency (gap_amount = required - student)
      - missing: student_proficiency == 0 (gap_amount = required)

    Learning Priority for missing/partial:
      1. Larger proficiency gap (primary key)
      2. Higher job weight (secondary key)
      Priority level:
        - "High": gap_amount >= 2.0 or weight >= 2.0
        - "Medium": gap_amount >= 1.0
        - "Low": otherwise
    """
    if not required_skills:
        return 100.0, [], [], [], [], "No specific required skills listed for this opportunity."

    matched_skills: List[SkillGapAnalysisItem] = []
    partial_skills: List[SkillGapAnalysisItem] = []
    missing_skills: List[SkillGapAnalysisItem] = []

    # Case-insensitive map of student skills
    lookup = {k.strip().lower(): float(v) for k, v in student_skills.items()}

    total_weight = 0.0
    total_weighted_score = 0.0

    for item in required_skills:
        if isinstance(item, str):
            skill_name = item.strip()
            req_prof = 3.0
            weight = 1.0
        elif isinstance(item, dict):
            skill_name = str(item.get("name", "")).strip()
            req_raw = item.get("required_proficiency") or item.get("requiredProficiency") or item.get("minimumProficiency") or 3.0
            req_prof = float(req_raw)
            if req_prof > 5.0:
                req_prof = round(req_prof / 20.0, 1)
            req_prof = max(1.0, req_prof)
            weight = max(0.1, float(item.get("weight", 1.0)))
        else:
            skill_name = getattr(item, "name", str(item)).strip()
            req_raw = getattr(item, "required_proficiency", getattr(item, "minimumProficiency", 3.0))
            req_prof = float(req_raw)
            if req_prof > 5.0:
                req_prof = round(req_prof / 20.0, 1)
            req_prof = max(1.0, req_prof)
            weight = max(0.1, float(getattr(item, "weight", 1.0)))

        student_prof = lookup.get(skill_name.lower(), 0.0)
        if student_prof > 5.0:
            student_prof = round(student_prof / 20.0, 1)

        # Transparent weighted scoring: min(student / required, 1.0)
        skill_score = min(student_prof / req_prof, 1.0)
        weighted_score = skill_score * weight
        total_weight += weight
        total_weighted_score += weighted_score

        # Categorize
        if student_prof >= req_prof:
            gap_cat = "matched"
            gap_amount = 0.0
            priority = "Low"
            item_model = SkillGapAnalysisItem(
                skill=skill_name,
                current_proficiency=student_prof,
                required_proficiency=req_prof,
                gap_amount=gap_amount,
                gap_category=gap_cat,
                weight=weight,
                skill_score=round(skill_score, 4),
                weighted_score=round(weighted_score, 4),
                priority=priority,
            )
            matched_skills.append(item_model)
        elif student_prof > 0.0:
            gap_cat = "partial"
            gap_amount = round(req_prof - student_prof, 1)
            priority = "High" if (gap_amount >= 2.0 or weight >= 2.0) else ("Medium" if gap_amount >= 1.0 else "Low")
            item_model = SkillGapAnalysisItem(
                skill=skill_name,
                current_proficiency=student_prof,
                required_proficiency=req_prof,
                gap_amount=gap_amount,
                gap_category=gap_cat,
                weight=weight,
                skill_score=round(skill_score, 4),
                weighted_score=round(weighted_score, 4),
                priority=priority,
            )
            partial_skills.append(item_model)
        else:
            gap_cat = "missing"
            gap_amount = round(req_prof, 1)
            priority = "High" if (gap_amount >= 2.0 or weight >= 2.0) else ("Medium" if gap_amount >= 1.0 else "Low")
            item_model = SkillGapAnalysisItem(
                skill=skill_name,
                current_proficiency=0.0,
                required_proficiency=req_prof,
                gap_amount=gap_amount,
                gap_category=gap_cat,
                weight=weight,
                skill_score=round(skill_score, 4),
                weighted_score=round(weighted_score, 4),
                priority=priority,
            )
            missing_skills.append(item_model)

    overall_score = round((total_weighted_score / total_weight) * 100, 1) if total_weight > 0 else 100.0

    # Prioritize missing and partial skills:
    # 1. Larger proficiency gap (primary key)
    # 2. Higher job weight (secondary key)
    all_gaps = partial_skills + missing_skills
    all_gaps.sort(key=lambda x: (-x.gap_amount, -x.weight))

    # Explainable summary
    total_req = len(required_skills)
    if not all_gaps:
        explanation = (
            f"You are a 100% complete match! You meet or exceed all {total_req} required skills "
            f"for this opportunity."
        )
    else:
        top_gap = all_gaps[0]
        explanation = (
            f"You meet {len(matched_skills)} of {total_req} required skills with an overall weighted match of {overall_score}%. "
            f"Highest priority to develop: {top_gap.skill} ({top_gap.gap_category.capitalize()} with gap of {top_gap.gap_amount:.1f} / weight {top_gap.weight:.1f})."
        )

    return overall_score, matched_skills, partial_skills, missing_skills, all_gaps, explanation


def build_job_required_skills_payload(job_data: dict) -> List[dict]:
    """
    Canonical, single-source-of-truth conversion of a job document into the
    required-skills payload consumed by compute_weighted_job_match().

    Combines:
      - required_skills: full weight, as configured by the recruiter.
      - preferred_skills: folded in at a reduced weight (0.5) using the job's
        minimum_proficiency (default 3.0) as their required proficiency, so a
        candidate gets partial credit for nice-to-have skills without them
        outweighing hard requirements.

    IMPORTANT: This must be the ONLY place job-skill requirements are assembled
    for matching. Both the student-facing application flow (applications.py)
    and the recruiter-facing candidate ranking (recruiter.py) call this so a
    student and a recruiter always see an identical match score for the same
    job/candidate pair - there is no second, competing scoring formula.
    """
    payload: List[dict] = []

    required = job_data.get("required_skills") or job_data.get("requiredSkills") or []
    for item in required:
        if isinstance(item, str):
            payload.append({"name": item, "required_proficiency": 3.0, "weight": 1.0})
        elif isinstance(item, dict):
            payload.append(item)
        else:
            payload.append({
                "name": getattr(item, "name", str(item)),
                "required_proficiency": getattr(item, "required_proficiency", 3.0),
                "weight": getattr(item, "weight", 1.0),
            })

    min_prof = float(job_data.get("minimum_proficiency") or job_data.get("minimumProficiency") or 3.0)
    preferred = job_data.get("preferred_skills") or job_data.get("preferredSkills") or []
    existing_names = {str(p.get("name", "")).strip().lower() for p in payload if isinstance(p, dict)}
    for pref_name in preferred:
        if isinstance(pref_name, str) and pref_name.strip() and pref_name.strip().lower() not in existing_names:
            payload.append({"name": pref_name.strip(), "required_proficiency": min_prof, "weight": 0.5})

    return payload


@router.get("/job/{job_id}", response_model=JobMatchAnalysisResponse, summary="Analyze student skill gap for a specific job")
async def analyze_job_match(
    job_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Deterministic skill gap analysis between authenticated student's skills
    and a specific job listing using transparent weighted scoring:
      skill_score = min(student_proficiency / required_proficiency, 1.0)
      overall_score = (sum(weighted_scores) / total_weights) * 100
    """
    db = get_db()
    # 1. Fetch job
    job_doc = db.collection("jobs").document(job_id).get()
    if not job_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    job_data = job_doc.to_dict() or {}
    required_skills = build_job_required_skills_payload(job_data)

    # 2. Fetch student's real skills from users/{uid}/skills
    skills_docs = db.collection("users").document(current_user.uid).collection("skills").stream()
    student_skills: Dict[str, float] = {}
    for sdoc in skills_docs:
        sdata = sdoc.to_dict() or {}
        name = sdata.get("name")
        if name:
            student_skills[name] = float(sdata.get("proficiency", sdata.get("score", 3)))

    # 3. Calculate deterministic weighted match
    overall_score, matched, partial, missing, prioritized_gaps, explanation = compute_weighted_job_match(
        student_skills, required_skills
    )

    # Legacy skill_gaps format for backward compatibility
    legacy_gaps = [
        SkillGapItem(
            skill=g.skill,
            current=int(g.current_proficiency),
            required=int(g.required_proficiency),
            gap=int(g.gap_amount),
            priority=g.priority,
            demand=75,
            recommendedCourse=f"Mastering {g.skill}",
        )
        for g in prioritized_gaps
    ]

    total_req = len(required_skills)
    total_weights = sum(m.weight for m in (matched + partial + missing))

    return JobMatchAnalysisResponse(
        job_id=job_id,
        job_title=job_data.get("title", "Job"),
        company=job_data.get("company", "Company"),
        overall_score=overall_score,
        match_score=int(round(overall_score)),
        total_weight=round(total_weights, 1),
        total_required=total_req,
        total_matched=len(matched),
        matched_skills=matched,
        partial_skills=partial,
        missing_skills=missing,
        prioritized_gaps=prioritized_gaps,
        skill_gaps=legacy_gaps,
        explanation=explanation,
    )


def normalize_proficiency_to_comparison(student_val: int, req_val: int) -> tuple[int, int]:
    """
    Normalizes proficiencies if one is 1-5 scale and the other is 0-100 scale.
    Returns (student_normalized, required_normalized).
    """
    if req_val <= 5 and student_val > 5:
        student_converted = max(1, min(5, round(student_val / 20)))
        return student_converted, req_val
    elif student_val <= 5 and req_val > 5:
        return student_val * 20, req_val
    else:
        return student_val, req_val


def compute_skill_gap(
    student_skills: Dict[str, int],
    required_skills: List[dict],
) -> tuple[int, List[MatchedSkillItem], List[SkillGapItem]]:
    """
    Deterministic Skill Gap Algorithm for Role Benchmarks.
    """
    if not required_skills:
        return 100, [], []

    matched_skills: List[MatchedSkillItem] = []
    skill_gaps: List[SkillGapItem] = []

    lookup = {k.strip().lower(): v for k, v in student_skills.items()}

    for item in required_skills:
        skill_name = item.get("name", "").strip()
        req_prof = item.get("minimumProficiency", item.get("required", 75))

        curr_prof = lookup.get(skill_name.lower(), 0)
        s_norm, r_norm = normalize_proficiency_to_comparison(curr_prof, req_prof)

        if s_norm >= r_norm:
            matched_skills.append(
                MatchedSkillItem(
                    skill=skill_name,
                    currentProficiency=curr_prof,
                    requiredProficiency=req_prof,
                    matched=True,
                )
            )
        else:
            gap = r_norm - s_norm
            priority = "High" if gap >= 25 or (r_norm <= 5 and gap >= 2) else ("Medium" if gap >= 15 or (r_norm <= 5 and gap >= 1) else "Low")
            skill_gaps.append(
                SkillGapItem(
                    skill=skill_name,
                    current=curr_prof,
                    required=req_prof,
                    gap=gap if r_norm > 5 else gap * 20,
                    priority=priority,
                    demand=75,
                    recommendedCourse=RECOMMENDED_COURSES.get(skill_name, f"Mastering {skill_name}"),
                )
            )

    total_req = len(required_skills)
    match_score = round((len(matched_skills) / total_req) * 100) if total_req > 0 else 100

    return match_score, matched_skills, skill_gaps


@router.get("/role-benchmark", response_model=RoleBenchmarkResponse, summary="Analyze student skill gap against target role benchmark")
async def analyze_role_benchmark(
    role: Optional[str] = Query(None, description="Target role name (e.g. Full-Stack Developer)"),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Deterministic skill gap analysis against industry target role benchmarks.
    Used directly by the Student Dashboard and Skill Gap Page.
    """
    db = get_db()
    target_role = role or current_user.targetRole or "Full-Stack Developer"
    benchmark = ROLE_BENCHMARKS.get(target_role, ROLE_BENCHMARKS["Full-Stack Developer"])

    # Fetch student's real skills
    skills_docs = db.collection("users").document(current_user.uid).collection("skills").stream()
    student_skills: Dict[str, int] = {}
    for sdoc in skills_docs:
        sdata = sdoc.to_dict() or {}
        name = sdata.get("name")
        if name:
            student_skills[name] = sdata.get("proficiency", sdata.get("score", 50))

    required_list = [{"name": k, "minimumProficiency": v} for k, v in benchmark.items()]
    score, matched, gaps = compute_skill_gap(student_skills, required_list)

    avg_gap = round(sum(g.gap for g in gaps) / len(gaps)) if gaps else 0

    return RoleBenchmarkResponse(
        targetRole=target_role,
        careerReadiness=score,
        skillsBenchmarked=len(required_list),
        meetingBenchmark=len(matched),
        belowBenchmark=len(gaps),
        avgGap=avg_gap,
        gaps=gaps,
        strengths=matched,
    )


# ===================== CURRICULUM & COURSES =====================

@router.get("/curriculum/courses", response_model=List[CourseResponse], summary="List all curriculum courses and skill contributions")
async def list_curriculum_courses():
    """Retrieve curriculum courses showing how academic subjects map to industry skills."""
    try:
        db = get_db()
        docs = db.collection("courses").stream()
        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(CourseResponse(**data))
        return results
    except Exception as e:
        logger.error("Error retrieving courses: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch curriculum: {str(e)}",
        )


@router.post("/curriculum/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, summary="Add a course-to-skill mapping")
async def create_curriculum_course(
    course_in: CourseCreate,
    current_user: UserProfileResponse = Depends(require_faculty),
):
    """Add a new curriculum course with skill contributions. Requires faculty or admin role."""
    try:
        db = get_db()
        course_data = course_in.model_dump()
        new_ref = db.collection("courses").document()
        new_ref.set(course_data)
        course_data["id"] = new_ref.id
        return CourseResponse(**course_data)
    except Exception as e:
        logger.error("Error creating course: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add curriculum course: {str(e)}",
        )

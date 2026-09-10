from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

UserRole = Literal["student", "faculty", "recruiter", "institution", "admin", "mentor"]
SkillCategory = Literal["Technical", "Soft", "Domain", "Tools"]
SkillLevel = Literal["Beginner", "Intermediate", "Advanced", "Expert"]
OpportunityType = Literal["Internship", "Full-time", "Apprenticeship", "Project"]
WorkMode = Literal["Remote", "Hybrid", "On-site"]
ApplicationStatus = Literal["Applied", "Shortlisted", "Interview", "Offered", "Rejected"]


# ===================== USER & AUTH MODELS =====================

class SocialLinks(BaseModel):
    github: Optional[str] = ""
    linkedin: Optional[str] = ""
    portfolio: Optional[str] = ""


class EducationEntry(BaseModel):
    degree: str
    institution: str
    year: str
    score: Optional[str] = ""


class ProjectEntry(BaseModel):
    title: str
    description: str
    tech: List[str] = Field(default_factory=list)
    link: Optional[str] = "#"


class CertificationEntry(BaseModel):
    name: str
    issuer: str
    year: str
    verified: bool = False


class ExperienceEntry(BaseModel):
    role: str
    org: str
    period: str
    description: str


class UserProfileBase(BaseModel):
    name: str
    email: str
    role: UserRole = "student"
    phone: Optional[str] = ""
    avatar: Optional[str] = "https://i.pravatar.cc/150?img=47"
    institution: Optional[str] = ""
    institution_id: Optional[str] = ""
    department: Optional[str] = ""
    degree: Optional[str] = ""
    branch: Optional[str] = ""
    year: Optional[str] = ""
    cgpa: Optional[float] = 0.0
    rollNo: Optional[str] = ""
    location: Optional[str] = ""
    headline: Optional[str] = ""
    about: Optional[str] = ""
    targetRole: Optional[str] = "Full-Stack Developer"
    profileCompletion: Optional[int] = 0
    skillScore: Optional[int] = 0
    careerReadiness: Optional[int] = 0
    links: Optional[SocialLinks] = Field(default_factory=SocialLinks)
    education: Optional[List[EducationEntry]] = Field(default_factory=list)
    projects: Optional[List[ProjectEntry]] = Field(default_factory=list)
    certifications: Optional[List[CertificationEntry]] = Field(default_factory=list)
    experience: Optional[List[ExperienceEntry]] = Field(default_factory=list)
    target_companies: Optional[List[str]] = Field(default_factory=list)
    dream_companies: Optional[List[str]] = Field(default_factory=list)


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    institution: Optional[str] = None
    institution_id: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[str] = None
    cgpa: Optional[float] = None
    rollNo: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    targetRole: Optional[str] = None
    profileCompletion: Optional[int] = None
    skillScore: Optional[int] = None
    careerReadiness: Optional[int] = None
    links: Optional[SocialLinks] = None
    education: Optional[List[EducationEntry]] = None
    projects: Optional[List[ProjectEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None
    experience: Optional[List[ExperienceEntry]] = None
    target_companies: Optional[List[str]] = None
    dream_companies: Optional[List[str]] = None


class UserProfileResponse(UserProfileBase):
    uid: str
    verified: bool = False
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class AuthMeResponse(BaseModel):
    uid: str
    email: str
    name: str
    role: UserRole
    avatar: Optional[str] = None
    verified: bool = True
    profile: Optional[UserProfileResponse] = None


# ===================== SKILL & EVIDENCE MODELS =====================

EvidenceType = Literal["project", "certificate", "course", "assessment", "other"]

PROFICIENCY_LEVELS: Dict[int, str] = {
    1: "Beginner",
    2: "Basic",
    3: "Intermediate",
    4: "Advanced",
    5: "Expert",
}


class SkillEvidence(BaseModel):
    type: EvidenceType = "other"
    title: Optional[str] = ""
    url: Optional[str] = ""
    description: Optional[str] = ""
    verified: bool = False
    issuedBy: Optional[str] = ""
    issueDate: Optional[str] = ""


class SkillBase(BaseModel):
    name: str
    proficiency: int = Field(
        ...,
        ge=1,
        le=5,
        description="Numerical proficiency scale: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert",
    )
    category: SkillCategory = "Technical"
    source: Optional[str] = "manual"
    evidence: Optional[SkillEvidence] = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Numerical proficiency scale: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert",
    )
    category: Optional[SkillCategory] = None
    source: Optional[str] = None
    evidence: Optional[SkillEvidence] = None


class SkillResponse(BaseModel):
    skillId: str
    id: str
    name: str
    category: SkillCategory = "Technical"
    proficiency: int = Field(ge=1, le=5)
    level: str = "Intermediate"
    score: int = Field(description="Percentage score (0-100) derived from proficiency for UI compatibility")
    required: int = 75
    source: str = "manual"
    evidence: Optional[SkillEvidence] = None
    verified: bool = False
    trend: int = 0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class AssessmentQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    difficulty: int = 1


class AssessmentAnswer(BaseModel):
    questionId: str
    selectedOption: int


class AssessmentSubmission(BaseModel):
    skillName: str
    category: SkillCategory = "Technical"
    answers: List[AssessmentAnswer]


class AssessmentResultResponse(BaseModel):
    skillName: str
    category: SkillCategory
    proficiency: int = Field(ge=1, le=5)
    level: str
    scorePercentage: int
    totalQuestions: int
    correctCount: int
    explanation: str
    skill: SkillResponse



# ===================== JOB / INTERNSHIP MODELS =====================

class RequiredSkill(BaseModel):
    name: str
    required_proficiency: float = Field(
        default=3.0,
        ge=1.0,
        description="Required proficiency level on a 1-5 scale (1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert)",
    )
    weight: float = Field(default=1.0, ge=0.1, description="Importance weight of the required skill")
    minimumProficiency: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve proficiency
            req = data.get("required_proficiency") or data.get("requiredProficiency")
            min_p = data.get("minimumProficiency") or data.get("minimum_proficiency")
            
            val = req if req is not None else min_p
            if val is not None:
                val_num = float(val)
                # Convert 0-100 percentage scale to 1-5 scale if passed as percentage (e.g. 20-100)
                if val_num >= 20.0:
                    val_num = round(val_num / 20.0, 1)
                data["required_proficiency"] = val_num
            else:
                data["required_proficiency"] = 3.0

            # Backward compatibility minimumProficiency
            data["minimumProficiency"] = int(round(data["required_proficiency"] * 20.0))

            if "weight" not in data or data["weight"] is None:
                data["weight"] = 1.0
            else:
                data["weight"] = float(data["weight"])
        return data


JobStatus = Literal["draft", "published", "closed", "archived"]


class JobBase(BaseModel):
    title: str
    company: str
    description: str
    location: str
    employment_type: str = Field(default="Internship", description="Employment type: Internship, Full-time, etc.")
    type: Optional[str] = "Internship"
    workMode: WorkMode = "Hybrid"
    stipend: Optional[str] = "₹40,000/mo"
    logo: Optional[str] = "CO"
    required_skills: List[RequiredSkill] = Field(default_factory=list)
    requiredSkills: Optional[List[RequiredSkill]] = None
    preferred_skills: List[str] = Field(default_factory=list)
    preferredSkills: Optional[List[str]] = None
    minimum_proficiency: Optional[int] = 3
    application_url: Optional[str] = ""
    source: Optional[str] = "recruiter"
    deadline: Optional[str] = "31 Dec 2026"
    status: JobStatus = "published"
    recruiter_uid: Optional[str] = None
    company_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def synchronize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Align employment_type and type
            emp_type = data.get("employment_type") or data.get("employmentType") or data.get("type") or "Internship"
            data["employment_type"] = emp_type
            data["type"] = emp_type

            # Align required_skills and requiredSkills
            req = data.get("required_skills") if "required_skills" in data else data.get("requiredSkills")
            if req is not None:
                # If required_skills is a list of strings (legacy format), convert to list of RequiredSkill dicts
                normalized_req = []
                for item in req:
                    if isinstance(item, str):
                        normalized_req.append({"name": item, "required_proficiency": 3.0, "weight": 1.0})
                    else:
                        normalized_req.append(item)
                data["required_skills"] = normalized_req
                data["requiredSkills"] = normalized_req

            # Align preferred_skills and preferredSkills
            pref = data.get("preferred_skills") if "preferred_skills" in data else data.get("preferredSkills")
            if pref is not None:
                data["preferred_skills"] = pref
                data["preferredSkills"] = pref

            # Align application_url
            app_url = data.get("application_url") or data.get("applicationUrl") or ""
            data["application_url"] = app_url

            # Align minimum_proficiency
            min_p = data.get("minimum_proficiency") or data.get("minimumProficiency")
            if min_p is not None:
                data["minimum_proficiency"] = int(min_p)

            # Align status
            if "status" not in data or not data["status"]:
                data["status"] = "published"

            # Align recruiter_uid and createdBy
            r_uid = data.get("recruiter_uid") or data.get("createdBy")
            if r_uid:
                data["recruiter_uid"] = r_uid
        return data


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    type: Optional[str] = None
    workMode: Optional[WorkMode] = None
    stipend: Optional[str] = None
    logo: Optional[str] = None
    required_skills: Optional[List[RequiredSkill]] = None
    preferred_skills: Optional[List[str]] = None
    minimum_proficiency: Optional[int] = None
    application_url: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[JobStatus] = None


class JobResponse(JobBase):
    id: str
    job_id: Optional[str] = None
    createdBy: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    applicants: int = 0
    matchScore: Optional[int] = 0

    @model_validator(mode="before")
    @classmethod
    def set_job_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            doc_id = data.get("id") or data.get("job_id")
            if doc_id:
                data["id"] = str(doc_id)
                data["job_id"] = str(doc_id)
            if not data.get("updatedAt"):
                data["updatedAt"] = data.get("createdAt")
            if not data.get("recruiter_uid") and data.get("createdBy"):
                data["recruiter_uid"] = data.get("createdBy")
        return data


# ===================== SKILL GAP & MATCHING MODELS =====================

GapCategory = Literal["matched", "partial", "missing"]


class SkillGapAnalysisItem(BaseModel):
    skill: str
    current_proficiency: float
    required_proficiency: float
    gap_amount: float
    gap_category: GapCategory
    weight: float = 1.0
    skill_score: float = 1.0
    weighted_score: float = 1.0
    priority: Literal["High", "Medium", "Low"] = "Low"


class MatchedSkillItem(BaseModel):
    skill: str
    currentProficiency: int
    requiredProficiency: int
    matched: bool = True


class SkillGapItem(BaseModel):
    skill: str
    current: int
    required: int
    gap: int
    priority: Literal["High", "Medium", "Low"]
    demand: int = 75
    recommendedCourse: str = "Recommended Course"


class JobMatchAnalysisResponse(BaseModel):
    job_id: str
    job_title: str
    company: str
    overall_score: float = Field(description="Deterministic weighted match score percentage (0-100)")
    match_score: Optional[int] = Field(None, description="Rounded integer score for UI compatibility")
    total_weight: float
    total_required: int
    total_matched: int
    matched_skills: List[SkillGapAnalysisItem]
    partial_skills: List[SkillGapAnalysisItem]
    missing_skills: List[SkillGapAnalysisItem]
    prioritized_gaps: List[SkillGapAnalysisItem]
    skill_gaps: Optional[List[SkillGapItem]] = None
    explanation: str


class CandidateEvidenceSummary(BaseModel):
    evidence_id: str
    type: str
    title: str
    issuer: Optional[str] = ""
    verification_status: str
    skill_ids: List[str] = Field(default_factory=list)
    project_url: Optional[str] = ""
    source_url: Optional[str] = ""


class CandidateMatchItem(BaseModel):
    candidate_id: str
    name: str
    email: Optional[str] = ""
    targetRole: Optional[str] = ""
    overall_score: float
    match_score: int
    matched_skills: List[SkillGapAnalysisItem]
    partial_skills: List[SkillGapAnalysisItem]
    missing_skills: List[SkillGapAnalysisItem]
    explanation: str
    evidence: List[CandidateEvidenceSummary] = Field(default_factory=list)


class JobCandidatesResponse(BaseModel):
    job_id: str
    job_title: str
    company: str
    total_candidates: int
    candidates: List[CandidateMatchItem]


class JobMatchResponse(BaseModel):
    job_id: str
    job_title: str
    company: str
    match_score: int = Field(description="Deterministic percentage of required skills met (0-100)")
    matched_skills: List[MatchedSkillItem]
    skill_gaps: List[SkillGapItem]
    total_required: int
    total_matched: int


class RoleBenchmarkResponse(BaseModel):
    targetRole: str
    careerReadiness: int
    skillsBenchmarked: int
    meetingBenchmark: int
    belowBenchmark: int
    avgGap: int
    gaps: List[SkillGapItem]
    strengths: List[MatchedSkillItem]


# ===================== COURSE / CURRICULUM MODELS =====================

class CourseSkillContribution(BaseModel):
    skill: str
    contribution: int = Field(default=20, ge=1, le=100, description="Proficiency contribution points")


class CourseBase(BaseModel):
    courseCode: str
    courseName: str
    semester: str
    department: str
    skills: List[CourseSkillContribution] = Field(default_factory=list)
    description: Optional[str] = ""


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: str
    createdAt: Optional[str] = None


# ===================== LEARNING PATH MODELS (STEP 30) =====================

LearningPathSkillStatus = Literal["not_started", "in_progress", "completed"]
LearningPathStatus = Literal["active", "completed", "archived"]


class LearningPathSkillItem(BaseModel):
    skill_id: str
    skill_name: str
    current_proficiency: float
    required_proficiency: float
    gap: float
    job_weight: float
    priority: Literal["High", "Medium", "Low"]
    priority_score: float
    reason: str
    status: LearningPathSkillStatus = "not_started"


class LearningPathCreate(BaseModel):
    job_id: str


class LearningPathSkillUpdate(BaseModel):
    status: LearningPathSkillStatus


class LearningPathStatusUpdate(BaseModel):
    status: LearningPathStatus


class LearningPathResponse(BaseModel):
    path_id: str
    user_id: str
    target_job_id: str
    target_job_title: str
    target_company: str
    skills: List[LearningPathSkillItem]
    overall_match_before: float
    overall_match_after: Optional[float] = 100.0
    status: LearningPathStatus = "active"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


# ===================== EVIDENCE & PORTFOLIO MODELS (STEP 31) =====================

VerificationStatus = Literal["pending", "approved", "rejected"]


class EvidenceBase(BaseModel):
    type: EvidenceType = "project"
    title: str = Field(..., min_length=2, max_length=150, description="Title of project, certificate, or course")
    description: Optional[str] = Field(default="", max_length=2000, description="Description or abstract")
    skill_ids: List[str] = Field(default_factory=list, description="IDs or names of linked skills")
    issuer: Optional[str] = Field(default="", max_length=150, description="Issuing authority, organization, or university")
    issue_date: Optional[str] = Field(default="", max_length=50, description="Issue or completion date (YYYY-MM-DD)")
    credential_id: Optional[str] = Field(default="", max_length=150, description="Credential or license identifier")
    project_url: Optional[str] = Field(default="", max_length=500, description="URL of deployed application or live demonstration")
    source_url: Optional[str] = Field(default="", max_length=500, description="Repository or verification source URL")
    file_path: Optional[str] = Field(default=None, max_length=500, description="Secure file reference path")


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    type: Optional[EvidenceType] = None
    skill_ids: Optional[List[str]] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    credential_id: Optional[str] = None
    project_url: Optional[str] = None
    source_url: Optional[str] = None
    file_path: Optional[str] = None


class EvidenceReview(BaseModel):
    verification_status: VerificationStatus
    verification_notes: Optional[str] = Field(default="", max_length=1000)


class EvidenceResponse(EvidenceBase):
    evidence_id: str
    id: str
    user_id: str
    verification_status: VerificationStatus = "pending"
    verification_notes: Optional[str] = ""
    reviewer_id: Optional[str] = None
    submittedAt: Optional[str] = None
    reviewedAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


# ===================== FACULTY & MENTOR MODELS (STEP 33) =====================

MentorAssignmentStatus = Literal["active", "inactive"]


class MentorAssignmentBase(BaseModel):
    mentor_uid: str = Field(..., min_length=1, description="Firebase UID of the assigned mentor")
    student_uid: str = Field(..., min_length=1, description="Firebase UID of the assigned student")
    institution_id: Optional[str] = Field(default=None, max_length=150)
    status: MentorAssignmentStatus = "active"


class MentorAssignmentCreate(MentorAssignmentBase):
    pass


class MentorAssignmentResponse(MentorAssignmentBase):
    assignment_id: str
    id: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class MentorFeedbackBase(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000, description="Guidance, feedback or recommendations for the student")
    related_skill_id: Optional[str] = Field(default=None, max_length=150, description="Optional linked skill ID or name")
    related_learning_path_id: Optional[str] = Field(default=None, max_length=150, description="Optional linked learning path ID")


class MentorFeedbackCreate(MentorFeedbackBase):
    pass


class MentorFeedbackResponse(MentorFeedbackBase):
    feedback_id: str
    id: str
    student_uid: str
    mentor_uid: str
    mentor_name: Optional[str] = "Mentor"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class AssignedStudentSummary(BaseModel):
    student_uid: str
    name: str
    email: str
    avatar: Optional[str] = None
    targetRole: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    skill_count: int = 0
    pending_evidence_count: int = 0
    assignment_id: Optional[str] = None
    assignedAt: Optional[str] = None


class MentorInfo(BaseModel):
    uid: str
    name: str
    email: str
    avatar: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    role: str = "faculty"


class AssignedMentorResponse(BaseModel):
    assigned: bool
    mentor: Optional[MentorInfo] = None


class EvidenceReviewActionRequest(BaseModel):
    verification_status: VerificationStatus
    verification_notes: Optional[str] = Field(default="", max_length=1000)
    student_uid: Optional[str] = Field(default=None, description="Optional student UID to resolve evidence subcollection")


class PendingEvidenceItem(EvidenceResponse):
    student_name: Optional[str] = None
    student_email: Optional[str] = None


class StudentMentoringDetailResponse(BaseModel):
    student_uid: str
    profile: UserProfileResponse
    skills: List[SkillResponse]
    learning_paths: List[LearningPathResponse]
    evidence: List[EvidenceResponse]
    feedback: List[MentorFeedbackResponse]
    skill_gaps: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


# ===================== INSTITUTION ANALYTICS MODELS (STEP 34) =====================

class StudentOverviewMetrics(BaseModel):
    total_students: int = 0
    active_students: int = 0
    students_with_skills: int = 0
    students_with_learning_paths: int = 0


class SkillDistributionItem(BaseModel):
    name: str
    count: int
    average_proficiency: float
    category: str = "Technical"


class SkillAnalyticsMetrics(BaseModel):
    total_skills_recorded: int = 0
    most_common_skills: List[SkillDistributionItem] = Field(default_factory=list)
    proficiency_distribution: Dict[str, int] = Field(default_factory=dict)
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    common_skill_gaps: List[Dict[str, Any]] = Field(default_factory=list)


class LearningAnalyticsMetrics(BaseModel):
    total_learning_paths: int = 0
    paths_by_status: Dict[str, int] = Field(default_factory=dict)
    skills_by_status: Dict[str, int] = Field(default_factory=dict)
    common_priority_skills: List[Dict[str, Any]] = Field(default_factory=list)


class EvidenceAnalyticsMetrics(BaseModel):
    total_evidence_submissions: int = 0
    evidence_by_status: Dict[str, int] = Field(default_factory=dict)
    evidence_by_type: Dict[str, int] = Field(default_factory=dict)


class MentorshipAnalyticsMetrics(BaseModel):
    total_mentor_assignments: int = 0
    active_mentor_assignments: int = 0
    assigned_students_count: int = 0
    feedback_activity_count: int = 0
    pending_evidence_reviews: int = 0


class RecruitmentAnalyticsMetrics(BaseModel):
    relevant_jobs_count: int = 0
    average_match_score: float = 0.0
    top_demand_skills: List[Dict[str, Any]] = Field(default_factory=list)


class InstitutionAnalyticsResponse(BaseModel):
    institution_id: str
    institution_name: str
    generated_at: str
    student_overview: StudentOverviewMetrics
    skill_analytics: SkillAnalyticsMetrics
    learning_analytics: LearningAnalyticsMetrics
    evidence_analytics: EvidenceAnalyticsMetrics
    mentorship_analytics: MentorshipAnalyticsMetrics
    recruitment_analytics: RecruitmentAnalyticsMetrics


# ===================== STEP 40: DATA PROVENANCE =====================

class DataProvenance(BaseModel):
    source: str = "system_deterministic"
    source_url: Optional[str] = None
    data_status: Literal["available", "unavailable", "verified", "unverified"] = "available"
    retrieved_at: Optional[str] = None
    is_test_data: bool = False


# ===================== STEP 35: AI CAREER ASSISTANT =====================

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    job_id: Optional[str] = None


class AIChatResponse(BaseModel):
    reply: str
    grounded_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    provider: str = "grounded_rule_engine"
    data_available: bool = True
    provenance: DataProvenance = Field(default_factory=DataProvenance)


# ===================== STEP 36: QUIZ & ASSESSMENT ENHANCEMENT =====================

class QuizQuestionResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    skill: str


class QuizDetailResponse(BaseModel):
    skill_name: str
    total_questions: int
    questions: List[QuizQuestionResponse]
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="assessment_question_bank"))


class QuizSubmissionRequest(BaseModel):
    skill_name: str
    category: str = "Technical"
    answers: Dict[str, int] = Field(..., description="Mapping of question ID to selected option index")


class QuizResultResponse(BaseModel):
    assessment_id: str
    skill_name: str
    category: str
    total_questions: int
    correct_count: int
    score_percentage: float
    assessed_proficiency: float
    previous_proficiency: Optional[float] = None
    current_proficiency: float
    preserved_verified: bool = False
    explanation: str
    timestamp: str
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="deterministic_assessment_engine", data_status="verified"))


class AssessmentHistoryItem(BaseModel):
    assessment_id: str
    skill_name: str
    category: str
    score_percentage: float
    assessed_proficiency: float
    correct_count: int
    total_questions: int
    timestamp: str
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="deterministic_assessment_engine"))


# ===================== STEP 37: APPLICATIONS TRACKING =====================

JobApplicationStatus = Literal["applied", "under_review", "shortlisted", "rejected", "selected", "withdrawn"]

class JobApplicationCreate(BaseModel):
    job_id: str
    notes: Optional[str] = ""


class JobApplicationUpdateStatus(BaseModel):
    status: JobApplicationStatus
    feedback: Optional[str] = ""


class JobApplicationResponse(BaseModel):
    application_id: str
    student_uid: str
    student_name: Optional[str] = ""
    student_email: Optional[str] = ""
    job_id: str
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    location: Optional[str] = ""
    status: JobApplicationStatus = "applied"
    applied_at: str
    updated_at: str
    notes: Optional[str] = ""
    feedback: Optional[str] = ""
    match_score: Optional[float] = None
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="applications_registry"))


# ===================== STEP 38: NOTIFICATIONS & ACTIVITY =====================

NotificationType = Literal[
    "application_status_changed",
    "evidence_reviewed",
    "mentor_feedback",
    "job_match",
    "learning_path_created",
    "assessment_completed",
    "general",
]

class NotificationItem(BaseModel):
    notification_id: str
    uid: str
    type: NotificationType
    title: str
    message: str
    read: bool = False
    created_at: str
    related_id: Optional[str] = None
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="activity_system"))


class NotificationListResponse(BaseModel):
    notifications: List[NotificationItem]
    unread_count: int


# ===================== STEP 39: ADMIN & ROLE MANAGEMENT =====================

class AdminRoleUpdateRequest(BaseModel):
    role: UserRole
    department: Optional[str] = None
    institution_id: Optional[str] = None


class AdminUserSummary(BaseModel):
    uid: str
    email: str
    name: str
    role: UserRole
    institution: Optional[str] = ""
    institution_id: Optional[str] = ""
    department: Optional[str] = ""
    created_at: Optional[str] = ""
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="identity_provider"))


# ===================== JOB MARKET INTELLIGENCE MODELS =====================

MarketJobDataType = Literal["observed_posting", "verified_hiring"]
MarketTimeRange = Literal["current", "last_1_month", "last_3_months", "custom", "all"]


class MarketJobRecord(BaseModel):
    job_id: str
    company: str
    job_title: str
    country: Optional[str] = "India"
    state: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    required_skills: List[RequiredSkill] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience: Optional[str] = "0-2 years"
    employment_type: Optional[str] = "Full-time"
    posted_date: Optional[str] = None
    closing_date: Optional[str] = None
    source: str = "market_data_source"
    source_url: Optional[str] = None
    data_type: MarketJobDataType = "observed_posting"
    retrieved_at: Optional[str] = None
    updated_at: Optional[str] = None
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="job_market_registry"))


class MarketOverviewResponse(BaseModel):
    status: Literal["available", "empty", "unconfigured"]
    message: Optional[str] = None
    total_observed_postings: int = 0
    total_verified_hirings: int = 0
    unique_companies_count: int = 0
    unique_roles_count: int = 0
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    most_requested_skills: List[Dict[str, Any]] = Field(default_factory=list)
    employment_type_distribution: Dict[str, int] = Field(default_factory=dict)
    location_distribution: Dict[str, int] = Field(default_factory=dict)
    time_filter_applied: str = "last_3_months"
    location_filter_applied: Dict[str, Optional[str]] = Field(default_factory=dict)
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="market_intelligence_engine"))


class CompanyMarketSummary(BaseModel):
    company: str
    observed_postings: int = 0
    verified_hirings: int = 0
    unique_roles: int = 0
    locations: List[str] = Field(default_factory=list)
    top_skills: List[str] = Field(default_factory=list)
    is_target_company: bool = False
    is_dream_company: bool = False


class CompanyMarketDetailResponse(BaseModel):
    company: str
    status: Literal["available", "not_found", "unconfigured"]
    message: Optional[str] = None
    observed_postings_count: int = 0
    verified_hirings_count: int = 0
    roles_posted: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    required_skills: List[Dict[str, Any]] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_levels: List[str] = Field(default_factory=list)
    employment_types: List[str] = Field(default_factory=list)
    open_postings: List[MarketJobRecord] = Field(default_factory=list)
    posting_dates: List[str] = Field(default_factory=list)
    skill_frequency: List[Dict[str, Any]] = Field(default_factory=list)
    historical_activity: List[Dict[str, Any]] = Field(default_factory=list)
    is_target_company: bool = False
    is_dream_company: bool = False
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="market_company_analytics"))


class SkillDemandItem(BaseModel):
    skill: str
    observed_postings: int
    percentage: float


class SkillDemandResponse(BaseModel):
    status: Literal["available", "empty", "unconfigured"]
    message: Optional[str] = None
    total_postings_analyzed: int = 0
    skills: List[SkillDemandItem] = Field(default_factory=list)
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="market_skill_analytics"))


class MarketTrendItem(BaseModel):
    month: str
    observed_postings: int
    unique_companies: int
    top_skills: List[Dict[str, Any]] = Field(default_factory=list)
    top_roles: List[Dict[str, Any]] = Field(default_factory=list)


class MarketTrendsResponse(BaseModel):
    status: Literal["available", "insufficient_data", "unconfigured"]
    message: Optional[str] = None
    trends: List[MarketTrendItem] = Field(default_factory=list)
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="market_trend_analytics"))


class StudentMarketSkillGapResponse(BaseModel):
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    target_location: Optional[str] = None
    market_match_score: float
    matched_skills: List[SkillGapAnalysisItem] = Field(default_factory=list)
    partial_skills: List[SkillGapAnalysisItem] = Field(default_factory=list)
    missing_skills: List[SkillGapAnalysisItem] = Field(default_factory=list)
    market_priority_skills: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="market_gap_engine"))


class CompanyPreferenceRequest(BaseModel):
    company: str
    preference_type: Literal["target", "dream"]
    action: Literal["add", "remove"]


class MarketLocationOptionsResponse(BaseModel):
    countries: List[str] = Field(default_factory=list)
    states: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)






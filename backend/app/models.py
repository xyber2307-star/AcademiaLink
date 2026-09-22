from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Common URL pattern used to validate optional link/URL fields that are actually submitted by
# a client (never applied to fields that are populated from external/legacy data sources,
# where a stricter pattern could reject real historical values on read).
_URL_PATTERN = r"^(https?://[^\s]+)$"
_OPTIONAL_URL_PATTERN = r"^($|https?://[^\s]+)$"


class StrictRequestModel(BaseModel):
    """
    Base for models that represent an incoming API request body ONLY - never used to
    deserialize a stored Firestore document (verified per-model before adopting this base;
    see the comment above each such model). Enforces:
      - extra="forbid": any field the client sends that isn't declared is a 422, not silently
        dropped or coerced.
      - str_strip_whitespace: leading/trailing whitespace is trimmed before validation, so
        e.g. a title of "   " correctly fails a min_length check instead of passing.
      - str_max_length: a generous backstop ceiling on every string field that doesn't declare
        its own tighter Field(max_length=...) below, so no request field is ever truly
        unbounded even if a specific limit was missed.
    Individual fields still declare their own tighter min_length/max_length/pattern via
    Field() where a stricter shape is meaningful (e.g. a title is 1-150 chars, not 5000).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)


UserRole = Literal["student", "faculty", "recruiter", "institution", "admin", "mentor"]
InstitutionVerificationStatus = Literal["VERIFIED", "NOT_VERIFIED", "SOURCE_UNAVAILABLE"]
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
    # Canonical institution fields - never set directly by a client request model (see
    # UserProfileUpdate below, which deliberately omits these). Populated only by the
    # server in PUT /users/me after it validates institution_id against the authoritative
    # institution registry (app/services/institution_data.py). See docs/INSTITUTION_VERIFICATION.md.
    institutionCode: Optional[str] = None
    institutionState: Optional[str] = None
    institutionDistrict: Optional[str] = None
    institutionVerificationStatus: Optional[InstitutionVerificationStatus] = None
    institutionVerificationSource: Optional[str] = None
    institutionLastVerifiedAt: Optional[str] = None
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


class UserProfileUpdate(StrictRequestModel):
    """
    A user's self-service profile edit (PUT /users/me). Deliberately has NO `role` field -
    role changes are a separate, admin-only endpoint - so this schema itself is part of the
    privilege-escalation defense, not just a length/format check.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30, pattern=r"^[0-9+\-() .]*$")
    avatar: Optional[str] = Field(None, max_length=1000, pattern=_OPTIONAL_URL_PATTERN)
    # `institution` is free-text (kept for backward compatibility / institutions not yet
    # in the registry) - saving it alone always yields NOT_VERIFIED. `institution_id`, when
    # provided, must be a real id returned by GET /institutions/search - the server looks it
    # up and derives institutionCode/State/District/verificationStatus itself; those derived
    # fields are intentionally NOT settable here (see UserProfileBase comment above).
    institution: Optional[str] = Field(None, max_length=200)
    institution_id: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    degree: Optional[str] = Field(None, max_length=100)
    branch: Optional[str] = Field(None, max_length=100)
    year: Optional[str] = Field(None, max_length=20)
    cgpa: Optional[float] = Field(None, ge=0, le=10)
    rollNo: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
    headline: Optional[str] = Field(None, max_length=200)
    about: Optional[str] = Field(None, max_length=2000)
    targetRole: Optional[str] = Field(None, max_length=150)
    profileCompletion: Optional[int] = Field(None, ge=0, le=100)
    skillScore: Optional[int] = Field(None, ge=0, le=100)
    careerReadiness: Optional[int] = Field(None, ge=0, le=100)
    links: Optional[SocialLinks] = None
    education: Optional[List[EducationEntry]] = Field(None, max_length=50)
    projects: Optional[List[ProjectEntry]] = Field(None, max_length=100)
    certifications: Optional[List[CertificationEntry]] = Field(None, max_length=100)
    experience: Optional[List[ExperienceEntry]] = Field(None, max_length=100)
    target_companies: Optional[List[str]] = Field(None, max_length=100)
    dream_companies: Optional[List[str]] = Field(None, max_length=100)


# Roles a user may self-select at signup. Deliberately excludes "admin" and "mentor" -
# neither is offered by the registration UI, and both must only ever be granted by an
# existing admin via PATCH /admin/users/{uid}/role (AdminRoleUpdateRequest).
SelfRegisterableRole = Literal["student", "faculty", "recruiter", "institution"]


class RegisterCompleteRequest(StrictRequestModel):
    """
    PUT /users/me/register - the ONE place a client may supply a `role` at all, and only
    because get_current_user's auto-provisioning always defaults a brand-new account to
    "student" (itself a privilege-escalation defense - see UserProfileUpdate's docstring).
    The route applies this role only once per account (guarded by the `roleFinalized` flag
    on the Firestore document); every call after that silently no-ops the role field, so
    this can never be replayed to change an already-finalized account's role.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    role: SelfRegisterableRole
    institution: Optional[str] = Field(None, max_length=200)


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


# ===================== INSTITUTION REGISTRY / VERIFICATION MODELS =====================
# Backed by app/services/institution_data.py - a deterministic, non-AI lookup over a
# locally-cached authoritative dataset (AICTE Institute Permanent ID list). See
# docs/INSTITUTION_VERIFICATION.md for the full architecture and data-source notes.

class InstitutionSearchResult(BaseModel):
    institutionId: str
    aicteId: str
    name: str
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    verificationStatus: InstitutionVerificationStatus = "VERIFIED"
    verificationSource: str = "AICTE"


class InstitutionSearchResponse(BaseModel):
    results: List[InstitutionSearchResult]
    source: str
    sourceAvailable: bool
    datasetDate: Optional[str] = None


class InstitutionDetail(InstitutionSearchResult):
    sourceReference: Optional[str] = None
    datasetDate: Optional[str] = None
    programLevelApprovalChecked: bool = False


class InstitutionVerificationStatsResponse(BaseModel):
    """Admin-only aggregate, computed live from real users/{uid} documents - never a fake/static figure."""
    totalUsersWithInstitution: int
    verifiedCount: int
    notVerifiedCount: int
    sourceUnavailableCount: int
    distinctVerifiedInstitutions: int
    verificationSource: Optional[str] = "AICTE"
    computedAt: str


# ===================== SKILL & EVIDENCE MODELS =====================

EvidenceType = Literal["project", "certificate", "course", "assessment", "other"]

PROFICIENCY_LEVELS: Dict[int, str] = {
    1: "Beginner",
    2: "Basic",
    3: "Intermediate",
    4: "Advanced",
    5: "Expert",
}


# NOTE: SkillEvidence is reused both as request-input (inside SkillCreate/SkillUpdate below)
# AND to deserialize evidence already stored on a Firestore skill document
# (skills.py::serialize_skill does SkillEvidence(**evidence_dict) on real, possibly older,
# data) - it therefore does NOT use StrictRequestModel/extra="forbid", since a stray legacy
# field on an existing document must not turn a read into a 500. Field lengths are still
# capped as a sane backstop, which real data is expected to already satisfy.
class SkillEvidence(BaseModel):
    type: EvidenceType = "other"
    title: Optional[str] = Field(default="", max_length=200)
    url: Optional[str] = Field(default="", max_length=1000)
    description: Optional[str] = Field(default="", max_length=2000)
    verified: bool = False
    issuedBy: Optional[str] = Field(default="", max_length=200)
    issueDate: Optional[str] = Field(default="", max_length=50)


class SkillBase(StrictRequestModel):
    """Request-only (never used to deserialize a stored skill - see SkillResponse, which is a
    separate, standalone class built via explicit keyword construction in serialize_skill())."""

    name: str = Field(..., min_length=1, max_length=120)
    proficiency: int = Field(
        ...,
        ge=1,
        le=5,
        description="Numerical proficiency scale: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert",
    )
    category: SkillCategory = "Technical"
    source: Optional[str] = Field(default="manual", max_length=50)
    evidence: Optional[SkillEvidence] = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(StrictRequestModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    proficiency: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Numerical proficiency scale: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert",
    )
    category: Optional[SkillCategory] = None
    source: Optional[str] = Field(None, max_length=50)
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


# ===================== SKILL TAXONOMY (canonical skill/tool/discipline registry) =====================
# Distinct from SkillCategory above (a narrow axis - Technical/Soft/Domain/Tools - used on a
# STUDENT's individual skill record). This is the broader, admin-managed canonical registry
# living in Firestore collection 'skills', organized by discipline category/subcategory, so new
# skills can be added/edited without any frontend or backend redeploy.

SkillTaxonomyType = Literal["technical", "tool", "soft", "domain"]


class SkillTaxonomyEntry(BaseModel):
    id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    type: SkillTaxonomyType = "technical"
    description: Optional[str] = ""
    aliases: List[str] = Field(default_factory=list)
    relatedSkills: List[str] = Field(default_factory=list)
    parentSkill: Optional[str] = None
    assessmentAvailable: bool = False
    active: bool = True
    source: str = "seed"
    version: int = 1
    popularity: int = 0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class SkillTaxonomyCreate(StrictRequestModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    type: SkillTaxonomyType = "technical"
    description: Optional[str] = Field(default="", max_length=1000)
    aliases: List[str] = Field(default_factory=list, max_length=50)
    relatedSkills: List[str] = Field(default_factory=list, max_length=50)
    parentSkill: Optional[str] = Field(None, max_length=150)
    assessmentAvailable: bool = False


class SkillTaxonomyUpdate(StrictRequestModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    type: Optional[SkillTaxonomyType] = None
    description: Optional[str] = Field(None, max_length=1000)
    aliases: Optional[List[str]] = Field(None, max_length=50)
    relatedSkills: Optional[List[str]] = Field(None, max_length=50)
    parentSkill: Optional[str] = Field(None, max_length=150)
    assessmentAvailable: Optional[bool] = None
    active: Optional[bool] = None


class SkillTaxonomyCategoriesResponse(BaseModel):
    categories: List[str]
    subcategories_by_category: Dict[str, List[str]]


class SkillMergeRequest(StrictRequestModel):
    source_skill_id: str = Field(..., min_length=1, max_length=200)
    target_skill_id: str = Field(..., min_length=1, max_length=200)


class SkillReviewQueueItem(BaseModel):
    id: str
    term: str
    occurrences: int = 1
    example_context: Optional[str] = None
    status: Literal["pending", "approved", "rejected"] = "pending"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None




class AssessmentQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    difficulty: int = 1


class AssessmentAnswer(StrictRequestModel):
    questionId: str = Field(..., min_length=1, max_length=100)
    selectedOption: int = Field(..., ge=0, le=25)


class AssessmentSubmission(StrictRequestModel):
    skillName: str = Field(..., min_length=1, max_length=120)
    category: SkillCategory = "Technical"
    answers: List[AssessmentAnswer] = Field(..., min_length=1, max_length=50)


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

# NOTE: shared - used both as request input (inside JobCreate/JobUpdate) and to deserialize
# skills already stored on real job/market documents (RequiredSkill(**rs) in
# market_data_provider.py). Does NOT use StrictRequestModel/extra="forbid" for that reason.
class RequiredSkill(BaseModel):
    name: str = Field(..., max_length=150)
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
    """
    Strict on top of JobBase: extra="forbid" here only (NOT on JobBase, which JobResponse
    also inherits and builds via JobResponse(**firestore_doc) - a stray legacy field on an
    existing job document must not turn a read into a 500). Field constraints below narrow
    JobBase's untyped `str` declarations for the fields most worth bounding on the write path.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)

    title: str = Field(..., min_length=2, max_length=150)
    company: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=5000)
    location: str = Field(..., min_length=1, max_length=150)
    stipend: Optional[str] = Field("₹40,000/mo", max_length=50)
    logo: Optional[str] = Field("CO", max_length=10)
    required_skills: List[RequiredSkill] = Field(default_factory=list, max_length=50)
    preferred_skills: List[str] = Field(default_factory=list, max_length=50)
    minimum_proficiency: Optional[int] = Field(3, ge=1, le=5)
    application_url: Optional[str] = Field("", max_length=1000, pattern=_OPTIONAL_URL_PATTERN)
    deadline: Optional[str] = Field("31 Dec 2026", max_length=50)


class JobUpdate(StrictRequestModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    company: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    location: Optional[str] = Field(None, min_length=1, max_length=150)
    employment_type: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, max_length=50)
    workMode: Optional[WorkMode] = None
    stipend: Optional[str] = Field(None, max_length=50)
    logo: Optional[str] = Field(None, max_length=10)
    required_skills: Optional[List[RequiredSkill]] = Field(None, max_length=50)
    preferred_skills: Optional[List[str]] = Field(None, max_length=50)
    minimum_proficiency: Optional[int] = Field(None, ge=1, le=5)
    application_url: Optional[str] = Field(None, max_length=1000, pattern=_OPTIONAL_URL_PATTERN)
    deadline: Optional[str] = Field(None, max_length=50)
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

# NOTE: shared - reachable from CourseResponse(**data) over real Firestore course documents,
# so no extra="forbid" / min_length here; a generous max_length backstop only.
class CourseSkillContribution(BaseModel):
    skill: str = Field(..., max_length=120)
    contribution: int = Field(default=20, ge=1, le=100, description="Proficiency contribution points")


class CourseBase(BaseModel):
    courseCode: str = Field(..., max_length=50)
    courseName: str = Field(..., max_length=200)
    semester: str = Field(..., max_length=20)
    department: str = Field(..., max_length=150)
    skills: List[CourseSkillContribution] = Field(default_factory=list)
    description: Optional[str] = Field(default="", max_length=2000)


class CourseCreate(CourseBase):
    """Strict on top of CourseBase: extra="forbid" here only (CourseResponse also inherits
    CourseBase and is built via CourseResponse(**firestore_doc) in matching.py)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)

    courseCode: str = Field(..., min_length=1, max_length=50)
    courseName: str = Field(..., min_length=1, max_length=200)
    semester: str = Field(..., min_length=1, max_length=20)
    department: str = Field(..., min_length=1, max_length=150)
    skills: List[CourseSkillContribution] = Field(default_factory=list, max_length=100)


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


class LearningPathCreate(StrictRequestModel):
    job_id: str = Field(..., min_length=1, max_length=200)


class LearningPathSkillUpdate(StrictRequestModel):
    status: LearningPathSkillStatus


class LearningPathStatusUpdate(StrictRequestModel):
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
    """Strict on top of EvidenceBase: extra="forbid" here only (EvidenceResponse also inherits
    EvidenceBase and is built via EvidenceResponse(**firestore_doc) throughout evidence.py/
    faculty.py - a stray legacy field on an existing evidence document must not 500 on read)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)

    skill_ids: List[str] = Field(default_factory=list, max_length=50)
    project_url: Optional[str] = Field(default="", max_length=500, pattern=_OPTIONAL_URL_PATTERN)
    source_url: Optional[str] = Field(default="", max_length=500, pattern=_OPTIONAL_URL_PATTERN)


class EvidenceUpdate(StrictRequestModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    type: Optional[EvidenceType] = None
    skill_ids: Optional[List[str]] = Field(None, max_length=50)
    issuer: Optional[str] = Field(None, max_length=150)
    issue_date: Optional[str] = Field(None, max_length=50)
    credential_id: Optional[str] = Field(None, max_length=150)
    project_url: Optional[str] = Field(None, max_length=500, pattern=_OPTIONAL_URL_PATTERN)
    source_url: Optional[str] = Field(None, max_length=500, pattern=_OPTIONAL_URL_PATTERN)
    file_path: Optional[str] = Field(None, max_length=500)


class EvidenceReview(StrictRequestModel):
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
    mentor_uid: str = Field(..., min_length=1, max_length=200, description="Firebase UID of the assigned mentor")
    student_uid: str = Field(..., min_length=1, max_length=200, description="Firebase UID of the assigned student")
    institution_id: Optional[str] = Field(default=None, max_length=150)
    status: MentorAssignmentStatus = "active"


class MentorAssignmentCreate(MentorAssignmentBase):
    """Strict on top of MentorAssignmentBase: extra="forbid" here only (MentorAssignmentResponse
    also inherits this base and is built via MentorAssignmentResponse(**doc_data) in faculty.py)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)


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
    """Strict on top of MentorFeedbackBase: extra="forbid" here only (MentorFeedbackResponse
    also inherits this base and is built via MentorFeedbackResponse(**data) in faculty.py)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_max_length=5000)


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


class EvidenceReviewActionRequest(StrictRequestModel):
    verification_status: VerificationStatus
    verification_notes: Optional[str] = Field(default="", max_length=1000)
    student_uid: Optional[str] = Field(default=None, max_length=200, description="Optional student UID to resolve evidence subcollection")


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


class SkillRecommendationItem(BaseModel):
    skill: str
    reason: str
    market_frequency_percentage: Optional[float] = None
    priority: Literal["High", "Medium", "Low"] = "Medium"


class SkillRecommendationsResponse(BaseModel):
    target_role: Optional[str] = None
    current_skills: List[str] = Field(default_factory=list)
    recommendations: List[SkillRecommendationItem] = Field(default_factory=list)
    explanation: str
    provenance: DataProvenance = Field(default_factory=lambda: DataProvenance(source="skill_recommendation_engine"))


# ===================== STEP 35: AI CAREER ASSISTANT =====================

class AIChatRequest(StrictRequestModel):
    message: str = Field(..., min_length=1, max_length=2000)
    job_id: Optional[str] = Field(None, max_length=200)


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


class QuizSubmissionRequest(StrictRequestModel):
    skill_name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(default="Technical", max_length=50)
    answers: Dict[str, int] = Field(
        ..., min_length=1, max_length=50, description="Mapping of question ID to selected option index"
    )

    @model_validator(mode="after")
    def validate_answers_shape(self) -> "QuizSubmissionRequest":
        for question_id, selected_option in self.answers.items():
            if not (1 <= len(question_id) <= 100):
                raise ValueError(f"Invalid question id length: {question_id!r}")
            if not (0 <= selected_option <= 25):
                raise ValueError(f"selectedOption out of range for question {question_id!r}: {selected_option}")
        return self


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

class JobApplicationCreate(StrictRequestModel):
    job_id: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(default="", max_length=2000)


class JobApplicationUpdateStatus(StrictRequestModel):
    status: JobApplicationStatus
    feedback: Optional[str] = Field(default="", max_length=2000)


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

class AdminRoleUpdateRequest(StrictRequestModel):
    role: UserRole
    department: Optional[str] = Field(None, max_length=150)
    institution_id: Optional[str] = Field(None, max_length=150)


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
    most_demanded_role: Optional[str] = None
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    most_requested_skills: List[Dict[str, Any]] = Field(default_factory=list)
    employment_type_distribution: Dict[str, int] = Field(default_factory=dict)
    location_distribution: Dict[str, int] = Field(default_factory=dict)
    time_filter_applied: str = "last_3_months"
    location_filter_applied: Dict[str, Optional[str]] = Field(default_factory=dict)
    data_sources: Optional[str] = None
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


class CompanyPreferenceRequest(StrictRequestModel):
    company: str = Field(..., min_length=1, max_length=150)
    preference_type: Literal["target", "dream"]
    action: Literal["add", "remove"]


class MarketLocationOptionsResponse(BaseModel):
    countries: List[str] = Field(default_factory=list)
    states: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)






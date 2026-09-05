from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from app.core.security import Role

def utcnow():
    return datetime.now(timezone.utc)

class SkillLevel(int, Enum):
    NOVICE=1; DEVELOPING=2; COMPETENT=3; PROFICIENT=4; ADVANCED=5
class EvidenceStatus(str, Enum): PENDING="pending"; APPROVED="approved"; REJECTED="rejected"
class OpportunityStatus(str, Enum): DRAFT="draft"; OPEN="open"; CLOSED="closed"
class ApplicationStatus(str, Enum): SUBMITTED="submitted"; SHORTLISTED="shortlisted"; REJECTED="rejected"; WITHDRAWN="withdrawn"

class Skill(BaseModel):
    id: str; name: str; category: str="general"; description: str|None=None
class User(BaseModel):
    id: str; email: str|None=None; display_name: str; role: Role; institution_id: str|None=None; created_at: datetime=Field(default_factory=utcnow)
class StudentSkill(BaseModel):
    id: str; student_id: str; skill_id: str; proficiency: SkillLevel; score: float=Field(ge=0,le=100); verified_evidence_count: int=Field(default=0,ge=0); last_assessed_at: datetime|None=None
class AssessmentQuestion(BaseModel):
    id: str; skill_id: str; prompt: str; options: dict[str,str]; correct_option: str; points: float=Field(gt=0)
class Assessment(BaseModel):
    id: str; title: str; description: str|None=None; questions: list[AssessmentQuestion]; active: bool=True
class AssessmentResult(BaseModel):
    id: str; student_id: str; assessment_id: str; score: float=Field(ge=0,le=100); skill_scores: dict[str,float]; submitted_at: datetime=Field(default_factory=utcnow)
class Evidence(BaseModel):
    id: str; student_id: str; skill_id: str; title: str; description: str; storage_path: str|None=None; url: str|None=None; status: EvidenceStatus=EvidenceStatus.PENDING; reviewed_by: str|None=None; review_comment: str|None=None; submitted_at: datetime=Field(default_factory=utcnow); reviewed_at: datetime|None=None
class RequiredSkill(BaseModel):
    skill_id: str; minimum_level: SkillLevel; weight: float=Field(default=1.0,gt=0)
class Opportunity(BaseModel):
    id: str; recruiter_id: str; company_name: str; title: str; description: str; status: OpportunityStatus=OpportunityStatus.DRAFT; required_skills: list[RequiredSkill]=Field(default_factory=list); min_experience_months: int=Field(default=0,ge=0); education_keywords: list[str]=Field(default_factory=list); created_at: datetime=Field(default_factory=utcnow)
class CandidateProfile(BaseModel):
    id: str; student_id: str; experience_months: int=Field(default=0,ge=0); education: str|None=None
class MatchBreakdown(BaseModel):
    skill_id: str; required_level: SkillLevel; achieved_level: SkillLevel|None; normalized_match: float=Field(ge=0,le=1); reason: str
class MatchResult(BaseModel):
    student_id: str; opportunity_id: str; score: float=Field(ge=0,le=100); eligible: bool; breakdown: list[MatchBreakdown]; missing_skills: list[str]; explanation: str
class Application(BaseModel):
    id: str; opportunity_id: str; student_id: str; status: ApplicationStatus=ApplicationStatus.SUBMITTED; applied_at: datetime=Field(default_factory=utcnow)

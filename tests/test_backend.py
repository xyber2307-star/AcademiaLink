from app.models.domain import *

def test_proficiency_bands():
 from app.services.skill_service import proficiency
 assert proficiency(10)==SkillLevel.NOVICE;assert proficiency(25)==SkillLevel.DEVELOPING;assert proficiency(45)==SkillLevel.COMPETENT;assert proficiency(65)==SkillLevel.PROFICIENT;assert proficiency(90)==SkillLevel.ADVANCED

def test_matching_is_authoritative():
 from app.db.repositories import RepositorySet,MemoryRepository
 from app.services.matching_service import MatchingService
 from app.core.config import Settings
 r=RepositorySet({k:MemoryRepository() for k in ['users','skills','assessments','assessment_results','student_skills','evidence','opportunities','applications','candidate_profiles']})
 r.student_skills.upsert(StudentSkill(id='s:python',student_id='s',skill_id='python',proficiency=SkillLevel.PROFICIENT,score=70,verified_evidence_count=1))
 o=Opportunity(id='o',recruiter_id='r',company_name='ACME',title='Backend',description='API',status=OpportunityStatus.OPEN,required_skills=[RequiredSkill(skill_id='python',minimum_level=SkillLevel.COMPETENT)])
 x=MatchingService(r,Settings()).match('s',o);assert x.score>=70 and x.breakdown[0].normalized_match==1

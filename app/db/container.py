from functools import lru_cache
from app.core.config import get_settings
from app.db.repositories import MemoryRepository,FirestoreRepository,RepositorySet
from app.models.domain import User,Skill,Assessment,AssessmentResult,StudentSkill,Evidence,Opportunity,Application,CandidateProfile
@lru_cache
def get_repositories():
 s=get_settings(); types={'users':(User,'users'),'skills':(Skill,'skills'),'assessments':(Assessment,'assessments'),'assessment_results':(AssessmentResult,'assessment_results'),'student_skills':(StudentSkill,'student_skills'),'evidence':(Evidence,'evidence'),'opportunities':(Opportunity,'opportunities'),'applications':(Application,'applications'),'candidate_profiles':(CandidateProfile,'candidate_profiles')}
 if s.database_mode=='firestore':
  from firebase_admin import firestore
  c=firestore.client(); return RepositorySet({k:FirestoreRepository(col,m,c) for k,(m,col) in types.items()})
 return RepositorySet({k:MemoryRepository() for k in types})

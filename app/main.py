from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.dependencies import current_user,roles
from app.core.security import Role
from app.core.exceptions import DomainError
from app.db.container import get_repositories
from app.models.domain import Skill,Opportunity,OpportunityStatus,RequiredSkill,CandidateProfile
from app.services.skill_service import SkillService
from app.services.assessment_service import AssessmentService
from app.services.evidence_service import EvidenceService
from app.services.matching_service import MatchingService
from pydantic import BaseModel,Field
from uuid import uuid4

class SkillCreate(BaseModel): name:str=Field(min_length=2,max_length=100); category:str='general'; description:str|None=None
class Answer(BaseModel): question_id:str; option:str
class AssessmentSubmission(BaseModel): answers:list[Answer]
class EvidenceInput(BaseModel): skill_id:str; title:str; description:str; storage_path:str|None=None; url:str|None=None
class EvidenceReview(BaseModel): status:str; review_comment:str|None=None
class OpportunityInput(BaseModel): company_name:str; title:str; description:str; required_skills:list[RequiredSkill]; min_experience_months:int=Field(0,ge=0); education_keywords:list[str]=[]; status:OpportunityStatus=OpportunityStatus.DRAFT
class ProfileInput(BaseModel): experience_months:int=Field(0,ge=0); education:str|None=None

app=FastAPI(title='AcademiaLINK API',version='0.1.0'); settings=get_settings()
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
@app.exception_handler(DomainError)
async def domain_error(_,exc): return JSONResponse(status_code=exc.status_code,content={'detail':exc.detail})
@app.exception_handler(PermissionError)
async def permission_error(_,exc): return JSONResponse(status_code=403,content={'detail':str(exc)})
@app.get('/')
async def root(): return {'service':'AcademiaLINK API','status':'ok'}
@app.get('/api/v1/health')
async def health(): return {'status':'ok'}
@app.get('/api/v1/auth/me')
async def me(u=Depends(current_user)): return {'user_id':u.user_id,'role':u.role,'email':u.email,'institution_id':u.institution_id}
@app.get('/api/v1/skills')
async def list_skills(u=Depends(current_user),r=Depends(get_repositories)): return r.skills.list()
@app.post('/api/v1/skills')
async def create_skill(x:SkillCreate,u=Depends(roles(Role.ADMIN)),r=Depends(get_repositories)): return r.skills.upsert(Skill(id=str(uuid4()),**x.model_dump()))
@app.get('/api/v1/students/me/skills')
async def my_skills(u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)): return SkillService(r).skills(u.user_id)
@app.get('/api/v1/students/me/gaps')
async def my_gaps(u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)): return {'gaps':SkillService(r).gaps(u.user_id,[(x.skill_id,x.proficiency) for x in SkillService(r).skills(u.user_id)])}
@app.put('/api/v1/students/me/profile')
async def update_profile(x:ProfileInput,u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)):
 p=CandidateProfile(id=u.user_id,student_id=u.user_id,**x.model_dump()); return r.candidate_profiles.upsert(p)
@app.get('/api/v1/assessments')
async def assessments(u=Depends(current_user),r=Depends(get_repositories)): return [x for x in r.assessments.list() if x.active]
@app.post('/api/v1/assessments/{aid}/submit')
async def submit(aid:str,x:AssessmentSubmission,u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)): return AssessmentService(r).submit(u.user_id,aid,x.answers)
@app.get('/api/v1/evidence/me')
async def my_evidence(u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)): return [e for e in r.evidence.list() if e.student_id==u.user_id]
@app.post('/api/v1/evidence')
async def submit_evidence(x:EvidenceInput,u=Depends(roles(Role.STUDENT)),r=Depends(get_repositories)): return EvidenceService(r).submit(u.user_id,x.model_dump())
@app.patch('/api/v1/evidence/{eid}/review')
async def review_evidence(eid:str,x:EvidenceReview,u=Depends(roles(Role.FACULTY,Role.ADMIN)),r=Depends(get_repositories)):
 from app.models.domain import EvidenceStatus
 try: status=EvidenceStatus(x.status)
 except ValueError as e: raise DomainError('Invalid evidence status') from e
 return EvidenceService(r).review(eid,u.user_id,status,x.review_comment)
@app.post('/api/v1/opportunities')
async def create_opportunity(x:OpportunityInput,u=Depends(roles(Role.RECRUITER)),r=Depends(get_repositories)): return r.opportunities.upsert(Opportunity(id=str(uuid4()),recruiter_id=u.user_id,**x.model_dump()))
@app.get('/api/v1/opportunities')
async def list_opportunities(u=Depends(current_user),r=Depends(get_repositories)): return [o for o in r.opportunities.list() if o.status!=OpportunityStatus.CLOSED]
@app.get('/api/v1/opportunities/{oid}/match/{sid}')
async def match(oid:str,sid:str,u=Depends(current_user),r=Depends(get_repositories)):
 o=r.opportunities.get(oid)
 if not o: raise DomainError('Opportunity not found',404)
 if u.role==Role.STUDENT and u.user_id!=sid: raise PermissionError('Students can only inspect their own match')
 if u.role==Role.RECRUITER and u.user_id!=o.recruiter_id: raise PermissionError('Not allowed')
 return MatchingService(r,settings).match(sid,o)

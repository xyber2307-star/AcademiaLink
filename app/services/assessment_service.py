from datetime import datetime,timezone
from uuid import uuid4
from app.core.exceptions import DomainError
from app.services.skill_service import SkillService
class AssessmentService:
 def __init__(self,r):self.r=r
 def submit(self,sid,aid,answers):
  a=self.r.assessments.get(aid)
  if not a or not a.active:raise DomainError('Assessment not found or inactive',404)
  amap={x.question_id:x.option for x in answers}
  if len(amap)!=len(answers):raise DomainError('Duplicate answers are not allowed')
  qids={q.id for q in a.questions}
  if set(amap)-qids:raise DomainError('Unknown question')
  total=sum(q.points for q in a.questions); earned=0; se={}; st={}
  for q in a.questions:
   st[q.skill_id]=st.get(q.skill_id,0)+q.points
   if amap.get(q.id)==q.correct_option:earned+=q.points;se[q.skill_id]=se.get(q.skill_id,0)+q.points
  score=round(earned/total*100,2) if total else 0
  ss={k:round(se.get(k,0)/v*100,2) for k,v in st.items()}; now=datetime.now(timezone.utc)
  from app.models.domain import AssessmentResult
  result=AssessmentResult(id=str(uuid4()),student_id=sid,assessment_id=aid,score=score,skill_scores=ss,submitted_at=now);self.r.assessment_results.upsert(result)
  for k,v in ss.items():SkillService(self.r).set_score(sid,k,v,now)
  return result

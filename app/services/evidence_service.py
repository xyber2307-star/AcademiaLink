from uuid import uuid4
from app.core.exceptions import DomainError
from app.models.domain import Evidence,EvidenceStatus
class EvidenceService:
 def __init__(self,r):self.r=r
 def submit(self,sid,data):return self.r.evidence.upsert(Evidence(id=str(uuid4()),student_id=sid,**data))
 def review(self,eid,reviewer,status,comment):
  e=self.r.evidence.get(eid)
  if not e:raise DomainError('Evidence not found',404)
  if e.status==EvidenceStatus.APPROVED and status==EvidenceStatus.APPROVED:raise DomainError('Evidence is already approved',409)
  from datetime import datetime,timezone
  e.status=status;e.reviewed_by=reviewer;e.review_comment=comment;e.reviewed_at=datetime.now(timezone.utc);self.r.evidence.upsert(e)
  if status==EvidenceStatus.APPROVED:
   for s in self.r.student_skills.list():
    if s.student_id==e.student_id and s.skill_id==e.skill_id:s.verified_evidence_count+=1;self.r.student_skills.upsert(s)
  return e

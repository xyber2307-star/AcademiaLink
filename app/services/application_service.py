from uuid import uuid4
from app.core.exceptions import ConflictError,NotFoundError
from app.models.domain import Application
class ApplicationService:
 def __init__(self,r):self.r=r
 def apply(self,sid,oid):
  o=self.r.opportunities.get(oid)
  if not o:raise NotFoundError('Opportunity not found')
  if o.status.value!='open':raise ConflictError('Opportunity is not open')
  if any(a.student_id==sid and a.opportunity_id==oid and a.status.value!='withdrawn' for a in self.r.applications.list()):raise ConflictError('Already applied')
  return self.r.applications.upsert(Application(id=str(uuid4()),student_id=sid,opportunity_id=oid))

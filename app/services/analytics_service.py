from app.db.repositories import RepositorySet
class AnalyticsService:
 def __init__(self,r):self.r=r
 def institution(self,iid):
  students=[u for u in self.r.users.list() if u.institution_id==iid and u.role.value=='student'];ids={u.id for u in students}
  skills=[s for s in self.r.student_skills.list() if s.student_id in ids];results=[x for x in self.r.assessment_results.list() if x.student_id in ids];e=[x for x in self.r.evidence.list() if x.student_id in ids and x.status.value=='approved']
  return {'institution_id':iid,'student_count':len(students),'assessed_student_count':len({x.student_id for x in results}),'verified_evidence_count':len(e),'average_assessment_score':round(sum(x.score for x in results)/len(results),2) if results else 0,'skill_gaps':[{'skill_id':k,'student_count':len(v),'average_score':round(sum(x.score for x in v)/len(v),2),'average_proficiency':round(sum(x.proficiency.value for x in v)/len(v),2)} for k,v in self._group(skills).items()]}
 @staticmethod
 def _group(items):
  out={}
  for x in items:out.setdefault(x.skill_id,[]).append(x)
  return out

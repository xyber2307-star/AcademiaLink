from app.models.domain import SkillLevel

def proficiency(score):
 if score<20:return SkillLevel.NOVICE
 if score<40:return SkillLevel.DEVELOPING
 if score<60:return SkillLevel.COMPETENT
 if score<80:return SkillLevel.PROFICIENT
 return SkillLevel.ADVANCED
class SkillService:
 def __init__(self,r):self.r=r
 def set_score(self,sid,kid,score,when=None):
  from app.models.domain import StudentSkill
  old=next((x for x in self.r.student_skills.list() if x.student_id==sid and x.skill_id==kid),None)
  x=StudentSkill(id=f'{sid}:{kid}',student_id=sid,skill_id=kid,score=score,proficiency=proficiency(score),verified_evidence_count=old.verified_evidence_count if old else 0,last_assessed_at=when)
  return self.r.student_skills.upsert(x)
 def skills(self,sid):return [x for x in self.r.student_skills.list() if x.student_id==sid]
 def gaps(self,sid,requirements):
  current={x.skill_id:x for x in self.skills(sid)}; out=[]
  for kid,level in requirements:
   x=current.get(kid)
   if not x or x.proficiency<level:out.append({'skill_id':kid,'required_level':level,'current_level':x.proficiency if x else None,'score':x.score if x else 0})
  return out

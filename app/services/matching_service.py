from app.models.domain import SkillLevel
class MatchingService:
 def __init__(self,r,s):self.r=r;self.s=s
 def match(self,sid,o):
  skills={x.skill_id:x for x in self.r.student_skills.list() if x.student_id==sid}; breakdown=[];missing=[];sw=sum(x.weight for x in o.required_skills) or 1; total=0
  for req in o.required_skills:
   cur=skills.get(req.skill_id); achieved=cur.proficiency if cur else None; n=min((achieved.value if achieved else 0)/req.minimum_level.value,1);total+=n*req.weight
   if not cur or achieved<req.minimum_level:missing.append(req.skill_id);reason=f'Below required level {req.minimum_level.name.lower()}'
   else:reason=f'Meets required level {req.minimum_level.name.lower()}'
   breakdown.append({'skill_id':req.skill_id,'required_level':req.minimum_level,'achieved_level':achieved,'normalized_match':round(n,4),'reason':reason})
  profile=next((p for p in self.r.candidate_profiles.list() if p.student_id==sid),None); exp=profile.experience_months if profile else 0
  ec=1 if not o.min_experience_months else min(exp/o.min_experience_months,1); edu=1 if not o.education_keywords else (1 if profile and profile.education and any(k.lower() in profile.education.lower() for k in o.education_keywords) else 0)
  verified=sum(x.verified_evidence_count for x in skills.values());vc=min(verified/max(len(o.required_skills),1),1)
  score=100*(self.s.match_skill_weight*(total/sw)+self.s.match_experience_weight*ec+self.s.match_education_weight*edu+self.s.match_verified_evidence_weight*vc)
  from app.models.domain import MatchResult,MatchBreakdown
  return MatchResult(student_id=sid,opportunity_id=o.id,score=round(score,2),eligible=not missing and exp>=o.min_experience_months,breakdown=[MatchBreakdown(**x) for x in breakdown],missing_skills=missing,explanation=f'Backend match score is {score:.2f}. '+(('Missing or below-threshold skills: '+', '.join(missing)+'.') if missing else 'All required thresholds are met.'))

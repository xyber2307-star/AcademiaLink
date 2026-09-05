import httpx
class CopilotService:
 def __init__(self,r,s):self.r=r;self.s=s
 async def answer(self,sid,message):
  skills=[x for x in self.r.student_skills.list() if x.student_id==sid];ctx={'skills':[{'skill_id':x.skill_id,'score':x.score,'proficiency':x.proficiency.value} for x in skills]}
  if self.s.ai_provider=='disabled':return f'Your current backend profile shows {len(skills)} assessed skills. Prioritize the lowest-proficiency skills and use verified evidence to strengthen your profile.',ctx
  if not self.s.ai_base_url or not self.s.ai_api_key:raise RuntimeError('AI configuration is incomplete')
  async with httpx.AsyncClient(timeout=30) as c:
   r=await c.post(self.s.ai_base_url,json={'model':self.s.ai_model,'message':message,'context':ctx},headers={'Authorization':f'Bearer {self.s.ai_api_key}'});r.raise_for_status();return r.json().get('answer',''),ctx

import json
from app.core.config import Settings
from app.core.security import CurrentUser,Role
class FirebaseAuthAdapter:
 def __init__(self,s:Settings): self.s=s; self.auth=None
 def verify_token(self,token):
  if self.auth is None:
   import firebase_admin
   from firebase_admin import auth,credentials
   if not firebase_admin._apps:
    raw=self.s.firebase_service_account_json
    if not raw: raise RuntimeError("Firebase credentials are not configured")
    info=json.loads(raw) if raw.strip().startswith("{") else raw
    firebase_admin.initialize_app(credentials.Certificate(info))
   self.auth=auth
  try:d=self.auth.verify_id_token(token)
  except Exception as e: raise ValueError("Invalid authentication token") from e
  try:r=Role(d.get("role",Role.STUDENT.value))
  except ValueError as e: raise ValueError("Invalid role claim") from e
  return CurrentUser(d["uid"],r,d.get("email"),d.get("institution_id"),d)
class FirebaseStorageAdapter:
 def __init__(self,s): self.bucket=s.firebase_storage_bucket
 def evidence_path(self,user_id,filename): return f"evidence/{user_id}/{filename.replace('/','_').replace(chr(92),'_')}"

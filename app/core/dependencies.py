from fastapi import Depends,Header
from app.core.config import get_settings
from app.core.security import CurrentUser,Role
from app.db.container import get_repositories
from app.adapters.firebase_auth import FirebaseAuthAdapter

def current_user(authorization: str|None=Header(None),x_user_id:str|None=Header(None),x_user_role:str|None=Header(None),x_user_email:str|None=Header(None),x_institution_id:str|None=Header(None)):
 s=get_settings()
 if s.auth_mode=='development':
  if not x_user_id or not x_user_role: raise PermissionError('Development authentication requires X-User-Id and X-User-Role')
  try:r=Role(x_user_role.lower())
  except ValueError as e: raise PermissionError('Invalid development role') from e
  return CurrentUser(x_user_id,r,x_user_email,x_institution_id,{})
 if not authorization or not authorization.startswith('Bearer '): raise PermissionError('Bearer authentication required')
 return FirebaseAuthAdapter(s).verify_token(authorization[7:].strip())
def roles(*allowed):
 def dep(user=Depends(current_user)):
  if user.role not in allowed: raise PermissionError('Insufficient role')
  return user
 return dep
Repo=Depends(get_repositories)
User=Depends(current_user)

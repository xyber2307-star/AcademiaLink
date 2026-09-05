from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_name:str='AcademiaLINK API';app_env:str='development';auth_mode:str='development';database_mode:str='memory';cors_origins:list[str]=['http://localhost:5173','http://localhost:3000'];firebase_service_account_json:str|None=None;firebase_storage_bucket:str|None=None;ai_provider:str='disabled';ai_base_url:str|None=None;ai_api_key:str|None=None;ai_model:str|None=None;match_skill_weight:float=.70;match_experience_weight:float=.15;match_education_weight:float=.10;match_verified_evidence_weight:float=.05
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
@lru_cache
def get_settings():
 s=Settings()
 if s.app_env=='production' and s.auth_mode=='development':raise ValueError('Development authentication cannot run in production')
 return s

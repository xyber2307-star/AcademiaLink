from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AcademiaLINK API"
    app_env: str = "development"
    auth_mode: str = "development"
    database_mode: str = "memory"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    firebase_service_account_json: str | None = None
    firebase_storage_bucket: str | None = None
    ai_provider: str = "disabled"
    ai_base_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    match_skill_weight: float = 0.70
    match_experience_weight: float = 0.15
    match_education_weight: float = 0.10
    match_verified_evidence_weight: float = 0.05
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def normalized_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and settings.auth_mode == "development":
        raise ValueError("Development authentication cannot run in production")
    return settings

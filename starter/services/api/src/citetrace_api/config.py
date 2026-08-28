from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CITETRACE_",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    source_policy_profile: str = "lawful-open-or-user-upload"
    retention_profile: str = "standard-30d"


@lru_cache
def get_settings() -> Settings:
    return Settings()

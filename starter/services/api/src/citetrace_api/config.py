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

    database_url: str = "postgresql+psycopg://citetrace:citetrace@localhost:5432/citetrace"
    database_pool_size: int = Field(default=10, ge=1, le=50)
    database_pool_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "citetrace"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    maximum_upload_bytes: int = 104_857_600

    grobid_url: str = "http://localhost:8070"
    grobid_connect_timeout_seconds: float = 5.0
    grobid_read_timeout_seconds: float = 120.0
    grobid_max_attempts: int = 3
    grobid_max_response_bytes: int = 52428800


@lru_cache
def get_settings() -> Settings:
    return Settings()

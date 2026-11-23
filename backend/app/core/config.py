from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+pg8000://oss_pulse:oss_pulse_local@localhost:5432/oss_pulse"
    database_ssl: bool = False
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    github_max_pages: int = 3
    github_timeout_seconds: float = 15.0
    analysis_rate_limit_enabled: bool = True
    analysis_rate_limit_per_minute: int = Field(default=2, ge=1)
    analysis_rate_limit_per_hour: int = Field(default=10, ge=1)
    analysis_rate_limit_global_per_hour: int | None = Field(default=None, ge=1)
    analysis_cache_ttl_seconds: int = Field(default=21600, ge=0)
    report_retention_days: int = Field(default=90, ge=1)
    report_max_history_per_repository: int = Field(default=10, ge=1)
    analysis_proxy_secret: str | None = None
    analysis_trust_forwarded_for: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("analysis_rate_limit_global_per_hour", mode="before")
    @classmethod
    def empty_global_limit_uses_default(cls, value):
        return None if value == "" else value


settings = Settings()

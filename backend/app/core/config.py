from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    github_max_pages: int = 3
    github_timeout_seconds: float = 15.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

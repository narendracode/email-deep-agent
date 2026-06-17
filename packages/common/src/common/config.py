from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/emailagent"

    # Anthropic
    anthropic_api_key: str = ""

    # Gmail OAuth2
    gmail_credentials_json: str = "credentials.json"
    gmail_token_json: str = "token.json"
    gmail_fetch_hours: int = 24
    gmail_max_results: int = 100

    # App
    log_level: str = "INFO"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()

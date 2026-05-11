"""Application configuration via pydantic-settings.

All values are read from environment variables or a .env file.
No secrets or URLs are hardcoded anywhere in the application.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_debug: bool = True
    app_title: str = "Digital Twin Simulation API"
    app_version: str = "1.0.0"

    # Database
    database_url: str = "sqlite+aiosqlite:///./digital_twin.db"

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Simulation limits
    max_concurrent_simulations: int = 5

    # Reports
    reports_dir: str = "/tmp/digital_twin_reports"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """True when running in production mode."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

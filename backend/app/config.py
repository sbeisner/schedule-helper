"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Schedule Manager"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Server
    host: str = "127.0.0.1"
    port: int = 8765

    # Database
    database_path: str = str(Path.home() / ".schedule-manager" / "data.db")

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_credentials_path: Optional[str] = None
    google_token_path: str = str(Path.home() / ".schedule-manager" / "google_token.json")

    # Google Calendar
    google_calendar_id: Optional[str] = None

    # Google Sheets - Data Sources
    household_sheet_id: Optional[str] = None
    personal_sheet_id: Optional[str] = None
    work_sheet_id: Optional[str] = None
    academic_sheet_id: Optional[str] = None

    # Scheduling Preferences
    timezone: str = "America/New_York"
    work_start_hour: int = 9
    work_end_hour: int = 17
    protected_hours: Optional[str] = None

    # Security
    secret_key: str = "dev-secret-change-in-production"

    # CORS
    cors_origins: list[str] = ["http://localhost:4200", "http://localhost:8765"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

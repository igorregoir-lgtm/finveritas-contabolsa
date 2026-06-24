"""
Centralized, validated application settings using pydantic-settings.

Environment variables take precedence over .env values, which take precedence
over defaults. This module is imported by database setup and the API bootstrap.
"""

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and sensible defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: PostgresDsn | str = Field(
        default="postgresql://finveritas:demo@localhost:5432/finveritas",
        description="PostgreSQL connection string. Accepts a valid postgres:// or postgresql:// URL.",
    )
    api_host: str = Field(default="0.0.0.0", description="Host the API binds to.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Port the API binds to.")
    api_reload: bool = Field(default=False, description="Enable uvicorn auto-reload (dev only).")
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    secret_key: str = Field(default="dev-secret-change-in-production", description="Used for signed exports.")
    cors_allow_origins: str = Field(default="*", description="Comma-separated allowed origins; '*' allows all.")

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins as a list."""
        if self.cors_allow_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

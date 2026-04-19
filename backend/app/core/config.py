"""
Application settings loaded from environment variables / .env file.
All deployment differences (local vs server) are expressed here — never hardcoded elsewhere.
"""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Looks for .env in backend/ directory
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/app.db"

    # ── LLM Categorizer ───────────────────────────────────────────────────────
    llm_backend: Literal["ollama", "claude", "none"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_api_key: str = ""

    # ── File Storage ─────────────────────────────────────────────────────────
    storage_backend: Literal["local", "s3"] = "local"
    # pathlib.Path ensures correct separators on Windows
    storage_local_path: Path = Path("data") / "uploads"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""     # set for Cloudflare R2 or MinIO
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Accepts comma-separated string from env var; split into list below
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list (env var is a comma-separated string)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        # Convert relative sqlite paths to use forward slashes (safe on all platforms)
        # Absolute paths and PostgreSQL URLs are left untouched
        if v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
            relative = v.removeprefix("sqlite:///")
            # Keep as-is — SQLAlchemy handles the path relative to CWD
        return v


# Singleton — import this everywhere instead of instantiating Settings() again
settings = Settings()

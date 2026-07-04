from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path


# Global settings instance (lazy loaded)
_settings: Optional["Settings"] = None

_WEAK_JWT_SECRETS = frozenset({
    "change-this-in-production",
    "secret",
    "changeme",
    "your-secret-here",
})


def get_settings() -> "Settings":
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


class Settings(BaseSettings):
    """Application settings with singleton pattern via lru_cache."""

    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    mem0_api_key: Optional[str] = Field(None, env="MEM0_API_KEY")

    # Paths
    chromadb_path: str = Field("./data/chroma", env="CHROMADB_PATH")
    database_url: str = Field("sqlite:///./data/cannae.db", env="DATABASE_URL")

    # Security
    jwt_secret: str = Field(..., env="JWT_SECRET")
    cors_origins: List[str] = Field(
        default=["http://localhost:8000"],
        env="CORS_ORIGINS",
    )

    # Search service keys (moved from os.environ reads)
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")
    searxng_url: str = Field("https://searx.be", env="SEARXNG_URL")

    # Server
    app_host: str = Field("127.0.0.1", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")

    # Debug — defaults to False for production safety
    debug: bool = Field(False, env="DEBUG")

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        if v.lower() in _WEAK_JWT_SECRETS or len(v) < 16:
            raise ValueError(
                "JWT_SECRET is too weak — use a random string of at least "
                "16 characters (e.g. `python -c 'import secrets; print(secrets.token_urlsafe(32))'`)."
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
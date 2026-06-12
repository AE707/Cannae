from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


# Global settings instance (lazy loaded)
settings = None


def get_settings() -> "Settings":
    """Get cached settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings


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

    # Server
    app_host: str = Field("127.0.0.1", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")

    # Debug
    debug: bool = Field(True, env="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = False



# Global settings instance (lazy loaded)
settings = None
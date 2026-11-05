"""
NoteIQ Core Configuration
Validates environment variables and provides centralized application settings.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # App
    APP_NAME: str = Field(default="NoteIQ", description="Configurable product name")
    ENVIRONMENT: str = Field(default="development", description="development | staging | production | test")
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    BACKEND_URL: str = Field(default="http://localhost:8000")
    CORS_ORIGINS: Union[str, List[str]] = Field(default=["http://localhost:3000"])

    # Database & Cache
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://noteiq:noteiq@localhost:5432/noteiq",
        description="Async/Sync PostgreSQL connection string"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Auth
    JWT_SECRET: str = Field(
        default="noteiq-insecure-development-secret-key-32-chars-minimum",
        description="JWT secret key for signing tokens"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_EXPIRE_DAYS: int = Field(default=14)
    COOKIE_SECURE: bool = Field(default=False)

    # S3 Compatible Storage
    S3_ENDPOINT_URL: str = Field(default="http://localhost:9000")
    S3_BUCKET: str = Field(default="noteiq-files")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_REGION: str = Field(default="auto")
    SIGNED_URL_EXPIRE_SECONDS: int = Field(default=300)
    MAX_UPLOAD_MB: int = Field(default=25)

    # AI Provider Settings
    LLM_PROVIDER: str = Field(default="gemini", description="gemini | anthropic | openai | fake")
    LLM_API_KEY: str = Field(default="")
    LLM_MODEL_ANALYSIS: str = Field(default="gemini-2.5-flash")
    LLM_MODEL_CHAT: str = Field(default="gemini-2.5-flash")
    EMBEDDING_PROVIDER: str = Field(default="gemini", description="gemini | openai | fake")
    EMBEDDING_API_KEY: str = Field(default="")
    EMBEDDING_MODEL: str = Field(default="text-embedding-004")
    EMBEDDING_DIM: int = Field(default=768)
    ANALYSIS_RUBRIC_VERSION: str = Field(default="v1")

    # Limits & Flags
    CHAT_RATE_LIMIT_PER_HOUR: int = Field(default=60)
    UPLOAD_RATE_LIMIT_PER_DAY: int = Field(default=20)
    MAX_ANALYSIS_CHARS: int = Field(default=400000)
    CLAMAV_ENABLED: bool = Field(default=False)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def validate_production_readiness(self) -> None:
        """Validates critical secrets when running in staging or production."""
        errors: List[str] = []
        if self.ENVIRONMENT in ("production", "staging"):
            if "change-me" in self.JWT_SECRET or len(self.JWT_SECRET) < 32:
                errors.append("JWT_SECRET must be at least 32 random characters in production.")
            if not self.COOKIE_SECURE:
                errors.append("COOKIE_SECURE must be true in production.")
            if self.LLM_PROVIDER != "fake" and not self.LLM_API_KEY:
                errors.append(f"LLM_API_KEY is required for provider {self.LLM_PROVIDER}.")
            if self.EMBEDDING_PROVIDER != "fake" and not (self.EMBEDDING_API_KEY or self.LLM_API_KEY):
                errors.append(f"EMBEDDING_API_KEY is required for embedding provider {self.EMBEDDING_PROVIDER}.")
        if errors:
            raise ValueError("Configuration Validation Error:\n - " + "\n - ".join(errors))


settings = Settings()

from typing import List, Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "AI Learning & Career Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Network
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "learning_platform_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_dev_password"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    POSTGRES_POOL_TIMEOUT: int = 30
    DATABASE_URL_OVERRIDE: Optional[str] = Field(default=None, alias="DATABASE_URL")

    @computed_field
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_dev_password"
    REDIS_DB: int = 0
    REDIS_TIMEOUT: int = 5
    REDIS_URL_OVERRIDE: Optional[str] = Field(default=None, alias="REDIS_URL")

    @computed_field
    @property
    def redis_url(self) -> str:
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Ollama / Local LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECONDS: int = 60
    LLM_INSTRUCTION_MODEL: str = "llama3:latest"
    LLM_REASONING_MODEL: str = "qwen2.5-coder:7b"
    LLM_EMBEDDING_MODEL: str = "bge-base-en-v1.5"

    # Security
    SECRET_KEY: str = "dev_secret_key_antigravity_platform_2026_test_only_min_32_chars!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"


settings = Settings()

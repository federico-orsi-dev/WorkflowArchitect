from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "WorkflowArchitect"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 60
    llm_timeout_seconds: int = 30

    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    enable_tracing: bool = False

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError(
                "OPENAI_API_KEY is required at startup. "
                "Set it in backend/.env or env vars."
            )
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

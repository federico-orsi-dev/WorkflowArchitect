from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",),
    )

    app_name: str = "WorkflowArchitect"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 60
    llm_timeout_seconds: int = 30

    openai_api_key: str | None = None
    model_name: str = "gpt-4o-mini"
    enable_tracing: bool = False

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "OPENAI_API_KEY is required at startup. " "Set it in backend/.env or env vars."
            )
        return normalized

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

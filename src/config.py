"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    """GeoStorm configuration — all fields optional so the app starts with zero env vars."""

    openrouter_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    slack_webhook_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "./data/geo-storm.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance populated from environment variables."""
    env_values: dict[str, str | int] = {}
    for field_name, field_info in Settings.model_fields.items():
        env_key = field_name.upper()
        raw = os.environ.get(env_key)
        if raw is not None:
            annotation = field_info.annotation
            if annotation is int or annotation == (int | None):
                env_values[field_name] = int(raw)
            else:
                env_values[field_name] = raw
    return Settings(**env_values)

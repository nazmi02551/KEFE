from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment/secret manager inputs."""

    model_config = SettingsConfigDict(env_prefix="KEFE_", extra="ignore")

    environment: str = "development"
    api_title: str = "KEFE API"
    api_version: str = "0.11.0"
    persistence_backend: Literal["memory", "postgres"] = "memory"
    database_url: str | None = None

    guest_token_ttl_days: int = 30
    guest_issue_rate_limit: int = 10
    guest_issue_rate_window_seconds: int = 60
    device_integrity_mode: Literal["OFF", "OPTIONAL", "REQUIRED"] = "OPTIONAL"

    event_transport: Literal["logging"] = "logging"
    outbox_batch_size: int = 100
    outbox_lease_seconds: int = 30
    outbox_poll_seconds: float = 1.0
    outbox_retry_base_seconds: int = 5
    outbox_retry_max_seconds: int = 900
    outbox_max_attempts: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()

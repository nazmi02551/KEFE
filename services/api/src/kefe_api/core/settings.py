from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment/secret manager inputs."""

    model_config = SettingsConfigDict(env_prefix="KEFE_", extra="ignore")

    environment: str = "development"
    api_title: str = "KEFE API"
    api_version: str = "0.3.0"
    persistence_backend: Literal["memory", "postgres"] = "memory"
    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

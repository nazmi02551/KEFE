from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET = (
    "development-only-guest-merge-replay-secret-v1"
)
DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID = "primary-v1"


class Settings(BaseSettings):
    """Runtime settings loaded from environment/secret manager inputs."""

    model_config = SettingsConfigDict(env_prefix="KEFE_", extra="ignore")

    environment: str = "development"
    api_title: str = "KEFE API"
    api_version: str = "0.19.0"
    persistence_backend: Literal["memory", "postgres"] = "memory"
    database_url: str | None = None

    guest_token_ttl_days: int = 30
    guest_issue_rate_limit: int = 10
    guest_issue_rate_window_seconds: int = 60
    device_integrity_mode: Literal["OFF", "OPTIONAL", "REQUIRED"] = "OPTIONAL"

    otp_challenge_ttl_minutes: int = 10
    otp_verification_ttl_minutes: int = 15
    otp_max_attempts: int = 5
    account_token_ttl_days: int = 30
    account_merge_replay_active_key_id: str = DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID
    account_merge_replay_secret: str = Field(
        default=DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET,
        min_length=32,
    )
    account_merge_replay_retained_keys: dict[str, str] = Field(default_factory=dict)
    share_ttl_days: int = 30

    event_transport: Literal["logging"] = "logging"
    outbox_batch_size: int = 100
    outbox_lease_seconds: int = 30
    outbox_poll_seconds: float = 1.0
    outbox_retry_base_seconds: int = 5
    outbox_retry_max_seconds: int = 900
    outbox_max_attempts: int = 8

    provider_http_runtime_mode: Literal["DISABLED", "PINNED_TLS"] = "DISABLED"
    provider_http_dns_max_answers: int = Field(default=16, ge=1, le=64)
    provider_http_ca_bundle_path: str | None = None

    raw_evidence_runtime_mode: Literal[
        "DISABLED",
        "EXTERNAL_DURABLE",
    ] = "DISABLED"
    raw_evidence_backend_profile_code: str | None = None

    @field_validator("provider_http_ca_bundle_path")
    @classmethod
    def validate_provider_http_ca_bundle_path(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("provider HTTP CA bundle path must not be blank")
        return value

    @field_validator("raw_evidence_backend_profile_code")
    @classmethod
    def validate_raw_evidence_backend_profile_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError(
                "raw evidence backend profile code must not be blank or padded"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

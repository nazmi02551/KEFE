from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET = (
    "development-only-guest-merge-replay-secret-v1"
)
DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID = "primary-v1"
_FORBIDDEN_PRODUCTION_DATABASE_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "10.0.2.2",
    }
)


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
    otp_delivery_mode: Literal["CAPTURE", "DISABLED", "HTTP"] = "CAPTURE"
    otp_http_endpoint: str | None = None
    otp_http_secret_ref: SecretStr | None = None
    otp_http_bearer_token: SecretStr | None = None
    otp_http_secret_lease_seconds: int = Field(default=30, ge=1, le=300)
    otp_http_timeout_ms: int = Field(default=3_000, ge=100, le=10_000)
    otp_http_max_response_bytes: int = Field(default=16_384, ge=1, le=65_536)
    otp_http_max_attempts: int = Field(default=2, ge=1, le=3)
    otp_delivery_health_window_seconds: int = Field(default=900, ge=60, le=86_400)
    otp_delivery_health_retention_seconds: int = Field(
        default=604_800,
        ge=900,
        le=2_592_000,
    )
    otp_delivery_health_minimum_ratio_sample: int = Field(
        default=5,
        ge=1,
        le=100_000,
    )
    otp_delivery_health_failure_attention: int = Field(default=3, ge=1, le=100_000)
    otp_delivery_health_failure_critical: int = Field(default=10, ge=1, le=100_000)
    otp_delivery_health_unavailable_attention: int = Field(default=2, ge=1, le=100_000)
    otp_delivery_health_unavailable_critical: int = Field(default=5, ge=1, le=100_000)
    otp_delivery_health_ratio_attention_bps: int = Field(default=2_000, ge=1, le=10_000)
    otp_delivery_health_ratio_critical_bps: int = Field(default=5_000, ge=1, le=10_000)
    otp_delivery_alert_cooldown_seconds: int = Field(default=1_800, ge=60, le=86_400)
    otp_delivery_alert_retention_seconds: int = Field(
        default=2_592_000,
        ge=3_600,
        le=7_776_000,
    )
    otp_receipt_mode: Literal["DISABLED", "HMAC_SHA256"] = "DISABLED"
    otp_receipt_secret_refs: dict[str, str] = Field(default_factory=dict)
    otp_receipt_secret_lease_seconds: int = Field(default=30, ge=1, le=300)
    otp_receipt_max_skew_seconds: int = Field(default=300, ge=30, le=3_600)
    otp_receipt_max_body_bytes: int = Field(default=4_096, ge=256, le=65_536)
    otp_receipt_retention_seconds: int = Field(
        default=2_592_000,
        ge=86_400,
        le=7_776_000,
    )
    otp_request_guard_mode: Literal["AUTO", "OFF", "ENFORCE"] = "AUTO"
    otp_request_cooldown_seconds: int = Field(default=60, ge=1, le=3_600)
    otp_request_window_seconds: int = Field(default=900, ge=60, le=86_400)
    otp_request_window_limit: int = Field(default=5, ge=1, le=100)
    otp_request_guard_retention_seconds: int = Field(
        default=86_400,
        ge=900,
        le=604_800,
    )

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

    @model_validator(mode="after")
    def validate_production_runtime(self) -> Settings:
        if self.environment.strip().lower() != "production":
            return self

        if self.persistence_backend != "postgres":
            raise ValueError("production requires KEFE_PERSISTENCE_BACKEND=postgres")
        if not self.database_url:
            raise ValueError("production requires KEFE_DATABASE_URL")

        database = urlsplit(self.database_url)
        if not database.scheme.startswith("postgresql") or not database.hostname:
            raise ValueError("production KEFE_DATABASE_URL must be a PostgreSQL network URL")
        hostname = database.hostname.lower()
        if hostname in _FORBIDDEN_PRODUCTION_DATABASE_HOSTS or hostname.endswith(".invalid"):
            raise ValueError("production KEFE_DATABASE_URL cannot target a local or reserved host")

        if self.account_merge_replay_secret == DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET:
            raise ValueError("production requires a non-development account merge replay secret")
        if DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET in self.account_merge_replay_retained_keys.values():
            raise ValueError("production cannot retain the development account merge replay secret")

        if self.otp_delivery_mode == "CAPTURE":
            raise ValueError("production forbids KEFE_OTP_DELIVERY_MODE=CAPTURE")
        if self.otp_request_guard_mode == "OFF":
            raise ValueError("production forbids KEFE_OTP_REQUEST_GUARD_MODE=OFF")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

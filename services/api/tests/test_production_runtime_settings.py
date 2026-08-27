from __future__ import annotations

import pytest
from pydantic import ValidationError

from kefe_api.core.settings import Settings

_VALID_PRODUCTION = {
    "environment": "production",
    "persistence_backend": "postgres",
    "database_url": "postgresql+psycopg://kefe:secret@db.internal:5432/kefe",
    "account_merge_replay_secret": "production-account-merge-replay-secret-0001",
    "session_renewal_secret": "production-session-renewal-secret-0000000001",
    "otp_delivery_mode": "DISABLED",
}


def _production_settings(**overrides: object) -> Settings:
    values = {**_VALID_PRODUCTION, **overrides}
    return Settings(**values)


def test_production_accepts_provider_neutral_postgres_runtime() -> None:
    settings = _production_settings()

    assert settings.persistence_backend == "postgres"
    assert settings.database_url == _VALID_PRODUCTION["database_url"]


@pytest.mark.parametrize("backend", ["memory"])
def test_production_rejects_in_memory_persistence(backend: str) -> None:
    with pytest.raises(ValidationError, match="KEFE_PERSISTENCE_BACKEND=postgres"):
        _production_settings(persistence_backend=backend)


def test_production_requires_database_url() -> None:
    with pytest.raises(ValidationError, match="KEFE_DATABASE_URL"):
        _production_settings(database_url=None)


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg://kefe:secret@localhost:5432/kefe",
        "postgresql+psycopg://kefe:secret@127.0.0.1:5432/kefe",
        "postgresql+psycopg://kefe:secret@10.0.2.2:5432/kefe",
        "postgresql+psycopg://kefe:secret@database.invalid:5432/kefe",
    ],
)
def test_production_rejects_local_or_reserved_database_hosts(database_url: str) -> None:
    with pytest.raises(ValidationError, match="local or reserved host"):
        _production_settings(database_url=database_url)


def test_production_rejects_non_postgres_database_url() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL network URL"):
        _production_settings(database_url="sqlite:///tmp/kefe.db")


def test_production_rejects_development_account_merge_secret() -> None:
    with pytest.raises(ValidationError, match="non-development account merge replay secret"):
        _production_settings(
            account_merge_replay_secret="development-only-guest-merge-replay-secret-v1"
        )


def test_production_rejects_retained_development_account_merge_secret() -> None:
    with pytest.raises(ValidationError, match="cannot retain the development"):
        _production_settings(
            account_merge_replay_retained_keys={
                "previous-v0": "development-only-guest-merge-replay-secret-v1"
            }
        )


def test_production_rejects_capturing_otp_adapter() -> None:
    with pytest.raises(ValidationError, match="KEFE_OTP_DELIVERY_MODE=CAPTURE"):
        _production_settings(otp_delivery_mode="CAPTURE")


def test_production_rejects_disabled_otp_abuse_guard() -> None:
    with pytest.raises(ValidationError, match="KEFE_OTP_REQUEST_GUARD_MODE=OFF"):
        _production_settings(otp_request_guard_mode="OFF")


def test_development_defaults_remain_available_for_local_and_unit_work() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.persistence_backend == "memory"
    assert settings.otp_delivery_mode == "CAPTURE"

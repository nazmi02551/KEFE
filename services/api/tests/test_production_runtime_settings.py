from __future__ import annotations

from pydantic import ValidationError
import pytest

from kefe_api.core.settings import Settings


_VALID_PRODUCTION = {
    "environment": "production",
    "persistence_backend": "postgres",
    "database_url": "postgresql+psycopg://kefe:secret@db.internal:5432/kefe",
    "account_merge_replay_secret": "production-account-merge-replay-secret-0001",
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


def test_production_rejects_missing_database_url() -> None:
    with pytest.raises(ValidationError, match="KEFE_DATABASE_URL is required"):
        _production_settings(database_url=None)


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite+pysqlite:///:memory:",
        "postgresql+psycopg://kefe:secret@localhost:5432/kefe",
        "postgresql+psycopg://kefe:secret@127.0.0.1:5432/kefe",
        "postgresql+psycopg://kefe:secret@10.0.2.2:5432/kefe",
        "postgresql+psycopg://kefe:secret@alpha-db.invalid:5432/kefe",
    ],
)
def test_production_rejects_non_network_or_reserved_database_targets(
    database_url: str,
) -> None:
    with pytest.raises(ValidationError):
        _production_settings(database_url=database_url)


def test_production_rejects_known_development_merge_secret() -> None:
    with pytest.raises(ValidationError, match="development account merge replay secret"):
        _production_settings(
            account_merge_replay_secret=(
                "development-only-account-merge-replay-secret-change-me"
            )
        )


def test_production_rejects_development_merge_secret_in_retained_keyring() -> None:
    with pytest.raises(ValidationError, match="development account merge replay secret"):
        _production_settings(
            account_merge_replay_keys=(
                "old=development-only-account-merge-replay-secret-change-me;"
                "future=production-account-merge-replay-secret-0002"
            )
        )


def test_production_rejects_otp_capture_mode() -> None:
    with pytest.raises(ValidationError, match="OTP capture mode"):
        _production_settings(otp_delivery_mode="CAPTURE")


def test_production_rejects_disabled_otp_abuse_guard() -> None:
    with pytest.raises(ValidationError, match="OTP request abuse guard"):
        _production_settings(otp_request_guard_mode="OFF")

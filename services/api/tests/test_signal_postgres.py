"""PostgreSQL integration tests for signal module.

Requires:
  KEFE_DATABASE_URL=postgresql+psycopg://kefe:kefe@localhost:5432/kefe
  KEFE_RUN_POSTGRES_TESTS=1

Tests the PostgresSignalRepository against a real PostgreSQL database
(migration 20260910_0042 must be applied).
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalDispatchStatus,
    SignalQualificationTier,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="Set KEFE_RUN_POSTGRES_TESTS=1 to run postgres integration tests",
)


def _make_signal(
    *,
    case_version_id: UUID | None = None,
    tier: SignalQualificationTier = SignalQualificationTier.BRONZE_OBSERVED,
) -> QualifiedSignal:
    return QualifiedSignal(
        signal_id=uuid4(),
        case_version_id=case_version_id or uuid4(),
        case_title="PostgreSQL integration test vakası",
        consensus_statement="Test editoryal ifade.",
        agreement_percentage=65.0,
        sample_size=250,
        qualification_tier=tier,
        methodology_version="1.0.0",
        qualification_audit_hash="e" * 64,
        certified_at=datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def pg_conn():
    """Provide a raw SQLAlchemy connection for signal integration tests."""
    from sqlalchemy import create_engine
    url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(url)
    with engine.connect() as conn:
        yield conn
        conn.rollback()


@pytest.fixture
def pg_signal_repo(pg_conn):
    from kefe_api.infrastructure.postgres_signal import PostgresSignalRepository
    return PostgresSignalRepository(pg_conn)


class TestPostgresSignalRepository:
    def test_save_and_get_signal(self, pg_signal_repo) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        fetched = pg_signal_repo.get_signal(signal.signal_id)
        assert fetched is not None
        assert fetched.signal_id == signal.signal_id
        assert fetched.qualification_tier == signal.qualification_tier
        assert fetched.sample_size == 250

    def test_list_signals_for_case(self, pg_signal_repo) -> None:
        case_id = uuid4()
        s1 = _make_signal(case_version_id=case_id)
        s2 = _make_signal(case_version_id=case_id)
        pg_signal_repo.save_qualified_signal(s1)
        pg_signal_repo.save_qualified_signal(s2)
        signals = pg_signal_repo.list_signals_for_case(case_id)
        ids = {s.signal_id for s in signals}
        assert s1.signal_id in ids
        assert s2.signal_id in ids

    def test_get_signal_not_found_returns_none(self, pg_signal_repo) -> None:
        missing = uuid4()
        result = pg_signal_repo.get_signal(missing)
        assert result is None

    def test_mark_signal_dispatched(self, pg_signal_repo) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()
        pg_signal_repo.mark_signal_dispatched(signal.signal_id, target_id)
        updated = pg_signal_repo.get_signal(signal.signal_id)
        assert updated is not None
        assert updated.dispatch_status == SignalDispatchStatus.DISPATCHED
        assert updated.dispatched_target_id == target_id
        assert updated.dispatched_at is not None

    def test_list_all_signals_pagination(self, pg_signal_repo) -> None:
        for _ in range(3):
            pg_signal_repo.save_qualified_signal(_make_signal())
        page1 = pg_signal_repo.list_all_signals(limit=2, offset=0)
        assert len(page1) <= 2

    def test_upsert_replaces_existing(self, pg_signal_repo) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        updated = QualifiedSignal(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            case_title=signal.case_title,
            consensus_statement="Güncellenmiş ifade.",
            agreement_percentage=72.0,
            sample_size=300,
            qualification_tier=SignalQualificationTier.SILVER_VALIDATED,
            methodology_version="1.0.0",
            qualification_audit_hash="f" * 64,
            certified_at=signal.certified_at,
        )
        pg_signal_repo.save_qualified_signal(updated)
        fetched = pg_signal_repo.get_signal(signal.signal_id)
        assert fetched is not None
        assert fetched.agreement_percentage == 72.0
        assert fetched.qualification_tier == SignalQualificationTier.SILVER_VALIDATED
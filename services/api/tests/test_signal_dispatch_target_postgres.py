"""PostgreSQL integration tests for signal dispatch target registry (CAP-057 Phase 2).

Requires:
  KEFE_DATABASE_URL=postgresql+psycopg://kefe:kefe@localhost:5432/kefe
  KEFE_RUN_POSTGRES_TESTS=1

Tests PostgresSignalDispatchTargetWriter + PostgresSignalDispatchTargetResolver
against a real PostgreSQL database (migrations 0042 + 0043 must be applied).
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    SignalTargetRegistryService,
    TargetType,
)
from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalQualificationTier,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="Set KEFE_RUN_POSTGRES_TESTS=1 to run postgres integration tests",
)

_ACTOR_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def _make_signal(case_version_id: UUID | None = None) -> QualifiedSignal:
    return QualifiedSignal(
        signal_id=uuid4(),
        case_version_id=case_version_id or uuid4(),
        case_title="Dispatch target postgres test vakası",
        consensus_statement="Test editoryal ifade — dispatch için.",
        agreement_percentage=70.0,
        sample_size=500,
        qualification_tier=SignalQualificationTier.SILVER_VALIDATED,
        methodology_version="1.0.0",
        qualification_audit_hash="a" * 64,
        certified_at=datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def pg_conn():
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


@pytest.fixture
def pg_writer(pg_conn):
    from kefe_api.infrastructure.postgres_signal_dispatch_target import (
        PostgresSignalDispatchTargetWriter,
    )
    return PostgresSignalDispatchTargetWriter(pg_conn)


@pytest.fixture
def pg_resolver(pg_conn):
    from kefe_api.infrastructure.postgres_signal_dispatch_target import (
        PostgresSignalDispatchTargetResolver,
    )
    return PostgresSignalDispatchTargetResolver(pg_conn)


class TestSignalDispatchTargetWriter:
    def test_propose_target_and_resolve(self, pg_signal_repo, pg_writer, pg_resolver) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)

        target_id = uuid4()
        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Postgres Test Kurum",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@test.gov.tr",
            response_due_days=30,
            proposed_by_actor_id=_ACTOR_ID,
        )

        targets = pg_resolver.resolve_targets(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            primary_domain_code="GOVERNANCE",
        )
        assert len(targets) == 1
        assert targets[0].target_id == target_id
        assert targets[0].dispatch_status == DispatchStatus.PROPOSED_TARGET

    def test_advance_proposed_to_verified(self, pg_signal_repo, pg_writer, pg_resolver) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()
        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Postgres Verified Test",
            target_type=TargetType.MINISTRY_DEPARTMENT,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@ministry.gov.tr",
        )

        result = pg_writer.advance_to_verified(
            signal_id=signal.signal_id,
            target_id=target_id,
            verified_by_actor_id=_ACTOR_ID,
        )
        assert result is True

        targets = pg_resolver.resolve_targets(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            primary_domain_code="GOVERNANCE",
        )
        assert targets[0].dispatch_status == DispatchStatus.VERIFIED_TARGET

    def test_full_lifecycle_proposed_to_dispatched(self, pg_signal_repo, pg_writer, pg_resolver) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()

        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Dispatch Lifecycle Test",
            target_type=TargetType.MUNICIPAL_GOVERNMENT,
            jurisdiction_level="MUNICIPAL",
            official_contact_ref="contact@mun.gov.tr",
        )
        pg_writer.advance_to_verified(
            signal_id=signal.signal_id,
            target_id=target_id,
            verified_by_actor_id=_ACTOR_ID,
        )
        dispatched = pg_writer.advance_to_dispatched(
            signal_id=signal.signal_id,
            target_id=target_id,
        )
        assert dispatched is True

        targets = pg_resolver.resolve_targets(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            primary_domain_code="GOVERNANCE",
        )
        assert targets[0].dispatch_status == DispatchStatus.DISPATCHED
        assert targets[0].dispatched_at is not None

    def test_decline_jurisdiction(self, pg_signal_repo, pg_writer, pg_resolver) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()

        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Declined Kurum",
            target_type=TargetType.CIVIC_OMBUDSMAN,
            jurisdiction_level="LOCAL",
            official_contact_ref="ombudsman@local.gov.tr",
        )
        declined = pg_writer.decline_jurisdiction(
            signal_id=signal.signal_id,
            target_id=target_id,
        )
        assert declined is True

        # DECLINED_JURISDICTION excluded from resolver
        targets = pg_resolver.resolve_targets(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            primary_domain_code="GOVERNANCE",
        )
        assert len(targets) == 0

    def test_advance_returns_false_when_wrong_status(self, pg_signal_repo, pg_writer) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()

        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Wrong Status Test",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@reg.gov.tr",
        )
        # Try to dispatch directly (skipping VERIFIED_TARGET)
        result = pg_writer.advance_to_dispatched(
            signal_id=signal.signal_id,
            target_id=target_id,
        )
        assert result is False

    def test_duplicate_target_raises_integrity_error(self, pg_signal_repo, pg_writer) -> None:
        from sqlalchemy.exc import IntegrityError
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()

        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Duplicate Test",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@reg.gov.tr",
        )
        with pytest.raises(IntegrityError):
            pg_writer.propose_target(
                signal_id=signal.signal_id,
                target_id=target_id,
                target_name="Duplicate Test Again",
                target_type=TargetType.REGULATORY_BODY,
                jurisdiction_level="NATIONAL",
                official_contact_ref="contact@reg.gov.tr",
            )


class TestSignalTargetRegistryServiceWithPostgres:
    def test_service_with_postgres_resolver(self, pg_signal_repo, pg_writer, pg_resolver) -> None:
        signal = _make_signal()
        pg_signal_repo.save_qualified_signal(signal)
        target_id = uuid4()

        pg_writer.propose_target(
            signal_id=signal.signal_id,
            target_id=target_id,
            target_name="Service Integration Test",
            target_type=TargetType.MINISTRY_DEPARTMENT,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@min.gov.tr",
        )
        pg_writer.advance_to_verified(
            signal_id=signal.signal_id,
            target_id=target_id,
            verified_by_actor_id=_ACTOR_ID,
        )

        service = SignalTargetRegistryService(resolver=pg_resolver)
        report = service.evaluate(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            primary_domain_code="GOVERNANCE",
        )

        assert len(report.targets) == 1
        assert len(report.dispatch_eligible_targets) == 1
        assert report.is_fully_dispatched is False
        assert len(report.registry_proof_hash) == 64
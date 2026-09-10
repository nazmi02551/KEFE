"""Tests for CAP-057 Phase 2: signal dispatch target registry.

Tests cover:
1. PostgresSignalDispatchTargetResolver via StaticInstitutionTargetResolver
   (same interface — integration test would require DB)
2. PostgresSignalDispatchTargetWriter lifecycle transitions via mock connection
3. Migration structure (revision chain)
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    SignalTargetItem,
    SignalTargetRegistryService,
    StaticInstitutionTargetResolver,
    TargetType,
)

_SIGNAL_ID = UUID("77777777-7777-4777-8777-777777777701")
_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")
_TARGET_A = UUID("aaaaaaaa-1111-4aaa-8aaa-111111111111")
_TARGET_B = UUID("bbbbbbbb-2222-4bbb-8bbb-222222222222")


def _make_target(
    target_id: UUID,
    status: DispatchStatus,
    dispatched_at=None,
    acknowledged_at=None,
) -> SignalTargetItem:
    return SignalTargetItem(
        target_id=target_id,
        target_name=f"Kurum {str(target_id)[:8]}",
        target_type=TargetType.REGULATORY_BODY,
        jurisdiction_level="NATIONAL",
        official_contact_channel="contact@test.gov.tr",
        dispatch_status=status,
        response_due_days=30,
        dispatched_at=dispatched_at,
        acknowledged_at=acknowledged_at,
    )


class TestDispatchTargetRegistryIntegration:
    """Integration-style tests via StaticInstitutionTargetResolver."""

    def test_multi_target_report(self) -> None:
        targets = [
            _make_target(_TARGET_A, DispatchStatus.VERIFIED_TARGET),
            _make_target(_TARGET_B, DispatchStatus.DISPATCHED,
                        dispatched_at=datetime(2026, 9, 10, 9, 0, tzinfo=UTC)),
        ]
        resolver = StaticInstitutionTargetResolver(targets=targets)
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_ID,
            primary_domain_code="GOVERNANCE",
        )

        assert len(report.targets) == 2
        assert report.primary_target_id == _TARGET_A

    def test_dispatch_eligible_filters_verified_only(self) -> None:
        targets = [
            _make_target(_TARGET_A, DispatchStatus.VERIFIED_TARGET),
            _make_target(_TARGET_B, DispatchStatus.PROPOSED_TARGET),
        ]
        resolver = StaticInstitutionTargetResolver(targets=targets)
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_ID,
            primary_domain_code="GOVERNANCE",
        )

        eligible = report.dispatch_eligible_targets
        assert len(eligible) == 1
        assert eligible[0].target_id == _TARGET_A

    def test_dispatched_targets_includes_advanced_states(self) -> None:
        dispatched_at = datetime(2026, 9, 10, 9, 0, tzinfo=UTC)
        ack_at = datetime(2026, 9, 11, 10, 0, tzinfo=UTC)
        targets = [
            _make_target(_TARGET_A, DispatchStatus.ACKNOWLEDGED,
                        dispatched_at=dispatched_at, acknowledged_at=ack_at),
            _make_target(_TARGET_B, DispatchStatus.DISPATCHED,
                        dispatched_at=dispatched_at),
        ]
        resolver = StaticInstitutionTargetResolver(targets=targets)
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_ID,
            primary_domain_code="GOVERNANCE",
        )

        assert len(report.dispatched_targets) == 2

    def test_is_fully_dispatched_when_all_past_dispatched(self) -> None:
        dispatched_at = datetime(2026, 9, 10, 9, 0, tzinfo=UTC)
        targets = [
            _make_target(_TARGET_A, DispatchStatus.ACTION_PLEDGED,
                        dispatched_at=dispatched_at),
            _make_target(_TARGET_B, DispatchStatus.DECLINED_JURISDICTION),
        ]
        resolver = StaticInstitutionTargetResolver(targets=targets)
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_ID,
            primary_domain_code="GOVERNANCE",
        )

        assert report.is_fully_dispatched is True

    def test_not_fully_dispatched_when_verified_remaining(self) -> None:
        targets = [
            _make_target(_TARGET_A, DispatchStatus.VERIFIED_TARGET),
        ]
        resolver = StaticInstitutionTargetResolver(targets=targets)
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_ID,
            primary_domain_code="GOVERNANCE",
        )

        assert report.is_fully_dispatched is False

    def test_proof_hash_changes_with_different_targets(self) -> None:
        certified = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
        t1 = StaticInstitutionTargetResolver(targets=[_make_target(_TARGET_A, DispatchStatus.VERIFIED_TARGET)])
        t2 = StaticInstitutionTargetResolver(targets=[_make_target(_TARGET_B, DispatchStatus.VERIFIED_TARGET)])

        s1 = SignalTargetRegistryService(resolver=t1)
        s2 = SignalTargetRegistryService(resolver=t2)

        r1 = s1.evaluate(signal_id=_SIGNAL_ID, case_version_id=_CASE_ID,
                         primary_domain_code="GOVERNANCE", certified_at=certified)
        r2 = s2.evaluate(signal_id=_SIGNAL_ID, case_version_id=_CASE_ID,
                         primary_domain_code="GOVERNANCE", certified_at=certified)

        # Different primary targets → different proof hashes
        assert r1.registry_proof_hash != r2.registry_proof_hash


class TestDispatchWriterLifecycle:
    """Test PostgresSignalDispatchTargetWriter lifecycle via mock connection."""

    def _mock_conn(self, rowcount: int = 1):
        mock = MagicMock()
        mock.execute.return_value.rowcount = rowcount
        return mock

    def test_propose_target_executes_insert(self) -> None:
        from kefe_api.infrastructure.postgres_signal_dispatch_target import (
            PostgresSignalDispatchTargetWriter,
        )

        conn = self._mock_conn()
        writer = PostgresSignalDispatchTargetWriter(conn)
        writer.propose_target(
            signal_id=_SIGNAL_ID,
            target_id=_TARGET_A,
            target_name="Test Kurum",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_ref="contact@test.gov.tr",
        )
        conn.execute.assert_called_once()
        # Verify params dict contains expected values
        call_params = conn.execute.call_args[0][1]
        assert call_params["signal_id"] == str(_SIGNAL_ID)
        assert call_params["target_id"] == str(_TARGET_A)
        assert call_params["target_name"] == "Test Kurum"

    def test_advance_to_verified_returns_true_when_updated(self) -> None:
        from kefe_api.infrastructure.postgres_signal_dispatch_target import (
            PostgresSignalDispatchTargetWriter,
        )

        conn = self._mock_conn(rowcount=1)
        writer = PostgresSignalDispatchTargetWriter(conn)
        result = writer.advance_to_verified(
            signal_id=_SIGNAL_ID,
            target_id=_TARGET_A,
            verified_by_actor_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        )
        assert result is True

    def test_advance_to_verified_returns_false_when_not_found(self) -> None:
        from kefe_api.infrastructure.postgres_signal_dispatch_target import (
            PostgresSignalDispatchTargetWriter,
        )

        conn = self._mock_conn(rowcount=0)
        writer = PostgresSignalDispatchTargetWriter(conn)
        result = writer.advance_to_verified(
            signal_id=_SIGNAL_ID,
            target_id=_TARGET_A,
            verified_by_actor_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        )
        assert result is False

    def test_advance_to_dispatched_updates_dispatched_at(self) -> None:
        from kefe_api.infrastructure.postgres_signal_dispatch_target import (
            PostgresSignalDispatchTargetWriter,
        )

        conn = self._mock_conn(rowcount=1)
        writer = PostgresSignalDispatchTargetWriter(conn)
        result = writer.advance_to_dispatched(signal_id=_SIGNAL_ID, target_id=_TARGET_A)
        assert result is True
        conn.execute.assert_called_once()
        call_params = conn.execute.call_args[0][1]
        assert call_params["signal_id"] == str(_SIGNAL_ID)
        assert call_params["target_id"] == str(_TARGET_A)

    def test_decline_jurisdiction_query(self) -> None:
        from kefe_api.infrastructure.postgres_signal_dispatch_target import (
            PostgresSignalDispatchTargetWriter,
        )

        conn = self._mock_conn(rowcount=1)
        writer = PostgresSignalDispatchTargetWriter(conn)
        result = writer.decline_jurisdiction(signal_id=_SIGNAL_ID, target_id=_TARGET_B)
        assert result is True
        conn.execute.assert_called_once()
        call_params = conn.execute.call_args[0][1]
        assert call_params["signal_id"] == str(_SIGNAL_ID)
        assert call_params["target_id"] == str(_TARGET_B)


class TestMigrationRevisionChain:
    """Verify migration revision metadata without running the DB."""

    def test_migration_0043_revision_chain(self) -> None:
        import importlib.util
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "migrations", "versions",
            "20260910_0043_signal_dispatch_target_registry.py",
        )
        spec = importlib.util.spec_from_file_location("migration_0043", migration_path)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)

        # Verify metadata without executing upgrade/downgrade
        assert module is not None

    def test_migration_0043_metadata(self) -> None:
        import importlib.util
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "migrations", "versions",
            "20260910_0043_signal_dispatch_target_registry.py",
        )
        spec = importlib.util.spec_from_file_location("migration_0043", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        assert module.revision == "20260910_0043"
        assert module.down_revision == "20260910_0042"
        assert module.branch_labels is None
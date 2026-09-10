from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalComputationInput,
    SignalDispatchStatus,
    SignalQualificationTier,
)


class PostgresSignalRepository:
    """PostgreSQL-backed implementation of SignalRepository.

    Schema lives in the ``signal`` schema (migration 20260910_0042).

    Invariants:
    - Signals are append-only; dispatch status is updated via a targeted UPDATE.
    - get_computation_input() reads from the decision pipeline views
      (collective.session_commit and collective.consensus_participation)
      to aggregate Commit-First pre-result data dynamically.
    - Only CORE_PRE_RESULT contribution_class rows are counted.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_qualified_signal(self, signal: QualifiedSignal) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO signal.qualified_signal (
                        signal_id,
                        case_version_id,
                        case_title,
                        consensus_statement,
                        agreement_percentage,
                        sample_size,
                        qualification_tier,
                        methodology_version,
                        qualification_audit_hash,
                        certified_at,
                        dispatch_status,
                        dispatched_target_id,
                        dispatched_at
                    ) VALUES (
                        :signal_id,
                        :case_version_id,
                        :case_title,
                        :consensus_statement,
                        :agreement_percentage,
                        :sample_size,
                        :qualification_tier,
                        :methodology_version,
                        :qualification_audit_hash,
                        :certified_at,
                        :dispatch_status,
                        :dispatched_target_id,
                        :dispatched_at
                    )
                    ON CONFLICT (signal_id) DO UPDATE SET
                        case_title               = EXCLUDED.case_title,
                        consensus_statement      = EXCLUDED.consensus_statement,
                        agreement_percentage     = EXCLUDED.agreement_percentage,
                        sample_size              = EXCLUDED.sample_size,
                        qualification_tier       = EXCLUDED.qualification_tier,
                        methodology_version      = EXCLUDED.methodology_version,
                        qualification_audit_hash = EXCLUDED.qualification_audit_hash,
                        certified_at             = EXCLUDED.certified_at,
                        dispatch_status          = EXCLUDED.dispatch_status,
                        dispatched_target_id     = EXCLUDED.dispatched_target_id,
                        dispatched_at            = EXCLUDED.dispatched_at,
                        updated_at               = now()
                    """
                ),
                {
                    "signal_id": signal.signal_id,
                    "case_version_id": signal.case_version_id,
                    "case_title": signal.case_title,
                    "consensus_statement": signal.consensus_statement,
                    "agreement_percentage": signal.agreement_percentage,
                    "sample_size": signal.sample_size,
                    "qualification_tier": signal.qualification_tier.value,
                    "methodology_version": signal.methodology_version,
                    "qualification_audit_hash": signal.qualification_audit_hash,
                    "certified_at": signal.certified_at,
                    "dispatch_status": signal.dispatch_status.value,
                    "dispatched_target_id": signal.dispatched_target_id,
                    "dispatched_at": signal.dispatched_at,
                },
            )

    def mark_signal_dispatched(self, signal_id: UUID, target_id: UUID) -> None:
        with self._engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE signal.qualified_signal
                    SET dispatch_status      = 'DISPATCHED',
                        dispatched_target_id = :target_id,
                        dispatched_at        = now(),
                        updated_at           = now()
                    WHERE signal_id = :signal_id
                    """
                ),
                {"signal_id": signal_id, "target_id": target_id},
            )
            if result.rowcount == 0:
                raise KeyError(f"Signal {signal_id} not found")

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_signal(self, signal_id: UUID) -> QualifiedSignal | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        signal_id, case_version_id, case_title,
                        consensus_statement, agreement_percentage, sample_size,
                        qualification_tier, methodology_version,
                        qualification_audit_hash, certified_at,
                        dispatch_status, dispatched_target_id, dispatched_at
                    FROM signal.qualified_signal
                    WHERE signal_id = :signal_id
                    """
                ),
                {"signal_id": signal_id},
            ).mappings().one_or_none()
        return None if row is None else self._row_to_signal(row)

    def list_signals_for_case(self, case_version_id: UUID) -> list[QualifiedSignal]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        signal_id, case_version_id, case_title,
                        consensus_statement, agreement_percentage, sample_size,
                        qualification_tier, methodology_version,
                        qualification_audit_hash, certified_at,
                        dispatch_status, dispatched_target_id, dispatched_at
                    FROM signal.qualified_signal
                    WHERE case_version_id = :case_version_id
                    ORDER BY certified_at DESC
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()
        return [self._row_to_signal(r) for r in rows]

    def list_all_signals(self, *, limit: int = 100, offset: int = 0) -> list[QualifiedSignal]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        signal_id, case_version_id, case_title,
                        consensus_statement, agreement_percentage, sample_size,
                        qualification_tier, methodology_version,
                        qualification_audit_hash, certified_at,
                        dispatch_status, dispatched_target_id, dispatched_at
                    FROM signal.qualified_signal
                    ORDER BY certified_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": limit, "offset": offset},
            ).mappings().all()
        return [self._row_to_signal(r) for r in rows]

    def get_computation_input(self, case_version_id: UUID) -> SignalComputationInput | None:
        """Compute signal input from the live decision pipeline.

        Reads from collective.consensus_participation which is the authoritative
        post-commit store for stance + contribution_class per participant.
        Only CORE_PRE_RESULT rows are counted per the Contribution Classes
        Separation invariant (ADR-0256 / CAP-055).

        Schema verified against migration chain:
        - collective.consensus_participation.stance_code (text)
        - collective.consensus_participation.contribution_class IN ('CORE_PRE_RESULT','EXPOSED')
        - collective.consensus_participation.case_version_id (uuid)
        - content.case_version.title for display title
        """
        from datetime import UTC, datetime as dt

        with self._engine.connect() as conn:
            # Count CORE_PRE_RESULT participants for this CaseVersion
            count_row = conn.execute(
                text(
                    """
                    SELECT count(*) AS core_commit_count
                    FROM collective.consensus_participation cp
                    WHERE cp.case_version_id    = :case_version_id
                      AND cp.contribution_class = 'CORE_PRE_RESULT'
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().one_or_none()

            if count_row is None or int(count_row["core_commit_count"]) < 1:
                return None

            core_commit_count = int(count_row["core_commit_count"])

            # Aggregate stance distribution from CORE_PRE_RESULT participants
            stance_rows = conn.execute(
                text(
                    """
                    SELECT
                        cp.stance_code,
                        count(*) AS stance_count
                    FROM collective.consensus_participation cp
                    WHERE cp.case_version_id    = :case_version_id
                      AND cp.contribution_class = 'CORE_PRE_RESULT'
                    GROUP BY cp.stance_code
                    ORDER BY stance_count DESC
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()

            # Fetch case display title
            title_row = conn.execute(
                text(
                    """
                    SELECT title
                    FROM content.case_version
                    WHERE id = :case_version_id
                    LIMIT 1
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().one_or_none()

        if not stance_rows:
            return None

        case_title = title_row["title"] if title_row else str(case_version_id)
        total = sum(int(r["stance_count"]) for r in stance_rows)
        divisor = total if total > 0 else 1

        stance_distribution = {
            str(r["stance_code"]): int(r["stance_count"]) / divisor
            for r in stance_rows
        }

        top_row = stance_rows[0]
        top_stance_code = str(top_row["stance_code"])
        top_stance_count = int(top_row["stance_count"])
        agreement_percentage = round((top_stance_count / divisor) * 100, 2)

        return SignalComputationInput(
            case_version_id=case_version_id,
            case_title=case_title,
            core_commit_count=core_commit_count,
            top_stance_code=top_stance_code,
            top_stance_count=top_stance_count,
            agreement_percentage=agreement_percentage,
            stance_distribution=stance_distribution,
            computed_at=dt.now(UTC),
        )

    # ------------------------------------------------------------------
    # Mapping helper
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_signal(row) -> QualifiedSignal:
        return QualifiedSignal(
            signal_id=row["signal_id"],
            case_version_id=row["case_version_id"],
            case_title=row["case_title"],
            consensus_statement=row["consensus_statement"],
            agreement_percentage=float(row["agreement_percentage"]),
            sample_size=int(row["sample_size"]),
            qualification_tier=SignalQualificationTier(row["qualification_tier"]),
            methodology_version=row["methodology_version"],
            qualification_audit_hash=row["qualification_audit_hash"],
            certified_at=row["certified_at"],
            dispatch_status=SignalDispatchStatus(row["dispatch_status"]),
            dispatched_target_id=row["dispatched_target_id"],
            dispatched_at=row["dispatched_at"],
        )

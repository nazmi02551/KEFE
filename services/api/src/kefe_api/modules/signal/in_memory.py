from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalComputationInput,
    SignalDispatchStatus,
)


class InMemorySignalRepository:
    """In-memory implementation of SignalRepository.

    Used in tests and memory persistence mode.
    Thread-safety is not guaranteed; intended for single-threaded use.
    """

    def __init__(self) -> None:
        self._signals: dict[UUID, QualifiedSignal] = {}
        self._computation_inputs: dict[UUID, SignalComputationInput] = {}

    def save_qualified_signal(self, signal: QualifiedSignal) -> None:
        self._signals[signal.signal_id] = signal

    def get_signal(self, signal_id: UUID) -> QualifiedSignal | None:
        return self._signals.get(signal_id)

    def list_signals_for_case(self, case_version_id: UUID) -> list[QualifiedSignal]:
        results = [
            s for s in self._signals.values()
            if s.case_version_id == case_version_id
        ]
        return sorted(results, key=lambda s: s.certified_at, reverse=True)

    def list_all_signals(self, *, limit: int = 100, offset: int = 0) -> list[QualifiedSignal]:
        sorted_all = sorted(
            self._signals.values(), key=lambda s: s.certified_at, reverse=True
        )
        return sorted_all[offset : offset + limit]

    def get_computation_input(self, case_version_id: UUID) -> SignalComputationInput | None:
        return self._computation_inputs.get(case_version_id)

    def mark_signal_dispatched(self, signal_id: UUID, target_id: UUID) -> None:
        signal = self._signals.get(signal_id)
        if signal is None:
            raise KeyError(f"Signal {signal_id} not found")
        updated = QualifiedSignal(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            case_title=signal.case_title,
            consensus_statement=signal.consensus_statement,
            agreement_percentage=signal.agreement_percentage,
            sample_size=signal.sample_size,
            qualification_tier=signal.qualification_tier,
            methodology_version=signal.methodology_version,
            qualification_audit_hash=signal.qualification_audit_hash,
            certified_at=signal.certified_at,
            dispatch_status=SignalDispatchStatus.DISPATCHED,
            dispatched_target_id=target_id,
            dispatched_at=datetime.now(UTC),
        )
        self._signals[signal_id] = updated

    # Test helper — not part of the SignalRepository protocol
    def seed_computation_input(self, inp: SignalComputationInput) -> None:
        """Inject a SignalComputationInput for testing without a live pipeline."""
        self._computation_inputs[inp.case_version_id] = inp
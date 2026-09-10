from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalComputationInput,
)


class SignalRepository(Protocol):
    """Hexagonal port for Signal persistence.

    Implementors: InMemorySignalRepository (test/memory),
    PostgresSignalRepository (production).

    Invariants:
    - Only CORE_PRE_RESULT (Commit-First, pre-reveal) contributions enter signal computation.
    - A QualifiedSignal is append-only; snapshots are never mutated in-place.
    - sample_size reflects only core pre-result commits (not exposed/advocacy classes).
    """

    def save_qualified_signal(self, signal: QualifiedSignal) -> None:
        """Persist or upsert a qualified signal record."""
        ...

    def get_signal(self, signal_id: UUID) -> QualifiedSignal | None:
        """Retrieve a single qualified signal by its ID."""
        ...

    def list_signals_for_case(self, case_version_id: UUID) -> list[QualifiedSignal]:
        """Return all qualified signals for a given CaseVersion, newest first."""
        ...

    def list_all_signals(self, *, limit: int = 100, offset: int = 0) -> list[QualifiedSignal]:
        """Return paginated list of all qualified signals, newest first."""
        ...

    def get_computation_input(self, case_version_id: UUID) -> SignalComputationInput | None:
        """Fetch aggregated Commit-First pre-result data needed to compute a signal.

        Returns None if the case has fewer than the minimum qualifying contributions
        or if the case does not exist.
        """
        ...

    def mark_signal_dispatched(self, signal_id: UUID, target_id: UUID) -> None:
        """Record that the signal has been dispatched to an institutional target."""
        ...
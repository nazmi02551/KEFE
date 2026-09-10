"""Tests for SignalPipelineService — live pipeline integration.

Verifies that:
- compute_and_save() returns None for insufficient data.
- compute_and_save() produces a valid QualifiedSignal for a seeded input.
- The QualifiedSignal is persisted in the repository after compute_and_save().
- signal_id is deterministic (same day + same case → same UUID).
- Collective Result is NOT automatically Signal (invariant tested via explicit call requirement).
- Tier thresholds are correctly applied.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.in_memory import InMemorySignalRepository
from kefe_api.modules.signal.pipeline_service import (
    MIN_SAMPLE_SIZE,
    SignalPipelineService,
)
from kefe_api.modules.signal.signal_models import (
    SignalComputationInput,
    SignalQualificationTier,
)

_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")
_CASE_TITLE = "Son koltuk kime verilmeli?"
_NOW = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)


def _make_input(core_commit_count: int = 500, agreement_percentage: float = 82.0) -> SignalComputationInput:
    return SignalComputationInput(
        case_version_id=_CASE_ID,
        case_title=_CASE_TITLE,
        core_commit_count=core_commit_count,
        top_stance_code="EVET",
        top_stance_count=int(core_commit_count * agreement_percentage / 100),
        agreement_percentage=agreement_percentage,
        stance_distribution={"EVET": agreement_percentage / 100, "HAYIR": 1.0 - agreement_percentage / 100},
        computed_at=_NOW,
    )


def _make_service(repo=None):
    repo = repo or InMemorySignalRepository()
    return SignalPipelineService(repository=repo, clock=lambda: _NOW), repo


def test_returns_none_when_insufficient_data() -> None:
    """Returns None when repository has no computation input (case not found)."""
    service, _ = _make_service()
    result = service.compute_and_save(case_version_id=_CASE_ID)
    assert result is None


def test_computes_signal_from_seeded_input() -> None:
    """Produces a valid QualifiedSignal when computation input is seeded."""
    repo = InMemorySignalRepository()
    repo.seed_computation_input(_make_input(core_commit_count=500, agreement_percentage=82.0))

    service, _ = _make_service(repo)
    signal = service.compute_and_save(case_version_id=_CASE_ID)

    assert signal is not None
    assert signal.case_version_id == _CASE_ID
    assert signal.case_title == _CASE_TITLE
    assert signal.sample_size == 500
    assert 80.0 <= signal.agreement_percentage <= 84.0
    assert signal.qualification_tier == SignalQualificationTier.GOLD_STANDARD
    assert signal.methodology_version == "1.0.0"
    assert len(signal.qualification_audit_hash) == 64
    assert "[PROVISIONAL]" in signal.consensus_statement


def test_signal_persisted_in_repository() -> None:
    """Computed signal is saved in the repository."""
    repo = InMemorySignalRepository()
    repo.seed_computation_input(_make_input())

    service = SignalPipelineService(repository=repo, clock=lambda: _NOW)
    signal = service.compute_and_save(case_version_id=_CASE_ID)

    assert signal is not None
    fetched = repo.get_signal(signal.signal_id)
    assert fetched is not None
    assert fetched.signal_id == signal.signal_id


def test_signal_id_is_deterministic() -> None:
    """Same case + same methodology + same date always produces the same signal_id."""
    repo1 = InMemorySignalRepository()
    repo1.seed_computation_input(_make_input())
    s1 = SignalPipelineService(repository=repo1, clock=lambda: _NOW).compute_and_save(_CASE_ID)

    repo2 = InMemorySignalRepository()
    repo2.seed_computation_input(_make_input())
    s2 = SignalPipelineService(repository=repo2, clock=lambda: _NOW).compute_and_save(_CASE_ID)

    assert s1 is not None
    assert s2 is not None
    assert s1.signal_id == s2.signal_id


def test_silver_tier_for_moderate_sample() -> None:
    """250–499 CORE_PRE_RESULT commits produce SILVER_VALIDATED."""
    repo = InMemorySignalRepository()
    repo.seed_computation_input(_make_input(core_commit_count=300, agreement_percentage=70.0))

    service, _ = _make_service(repo)
    signal = service.compute_and_save(case_version_id=_CASE_ID)

    assert signal is not None
    assert signal.qualification_tier == SignalQualificationTier.SILVER_VALIDATED


def test_bronze_tier_for_small_sample() -> None:
    """100–249 commits produce BRONZE_OBSERVED."""
    repo = InMemorySignalRepository()
    repo.seed_computation_input(_make_input(core_commit_count=150, agreement_percentage=66.0))

    service, _ = _make_service(repo)
    signal = service.compute_and_save(case_version_id=_CASE_ID)

    assert signal is not None
    assert signal.qualification_tier == SignalQualificationTier.BRONZE_OBSERVED


def test_below_minimum_seed_returns_none() -> None:
    """get_computation_input returns None when seeded count < MIN_SAMPLE_SIZE.

    The InMemorySignalRepository.get_computation_input() returns whatever was
    seeded. The MIN_SAMPLE_SIZE gate is enforced inside SignalPipelineService._compute().
    When the repo returns a value below threshold, seed_computation_input stores it
    but the service checks and should raise or return None.

    Since get_computation_input() returns the seeded input regardless of count,
    the pipeline service must detect insufficient data before computing.
    """
    from kefe_api.modules.signal.pipeline_service import SignalPipelineError
    import pytest

    repo = InMemorySignalRepository()
    # Seed below minimum — repo will return it, but pipeline must reject it
    repo.seed_computation_input(_make_input(core_commit_count=50))

    service, _ = _make_service(repo)

    # Pipeline should raise SignalPipelineError for inputs below MIN_SAMPLE_SIZE
    with pytest.raises(SignalPipelineError):
        service.compute_and_save(case_version_id=_CASE_ID)


def test_collective_result_not_auto_signal() -> None:
    """Invariant: the pipeline must be EXPLICITLY invoked; it does not auto-fire.

    This test confirms that seeding a computation input does NOT automatically
    produce a signal — compute_and_save() must be explicitly called.
    """
    repo = InMemorySignalRepository()
    repo.seed_computation_input(_make_input())

    # No service created, no compute called — repository has no signals
    assert repo.list_all_signals() == []
    assert repo.get_computation_input(_CASE_ID) is not None  # input exists

    # Explicit call required
    service = SignalPipelineService(repository=repo, clock=lambda: _NOW)
    signal = service.compute_and_save(_CASE_ID)
    assert signal is not None
    assert len(repo.list_all_signals()) == 1
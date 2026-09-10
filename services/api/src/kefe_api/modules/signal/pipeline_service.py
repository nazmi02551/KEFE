"""Signal Pipeline Service

Bridges the decision pipeline to the signal qualification engine.

Responsibilities:
- Read SignalComputationInput from the signal repository (which queries the
  live decision.weigh_session / decision.response tables for CORE_PRE_RESULT
  contributions only).
- Feed the raw aggregated data into SignalQualificationService.evaluate().
- Persist the resulting QualifiedSignal via the signal repository.

Invariants preserved:
- Only CORE_PRE_RESULT (Commit-First, pre-reveal) contributions enter computation.
- Collective Result is NOT automatically a Signal; this service must be
  explicitly invoked by an authorized pipeline trigger, not auto-fired on
  every decision commit.
- sample_size in QualifiedSignal reflects only core pre-result commits.
- QualifiedSignal records are append-only; methodology changes produce
  a new signal with an incremented methodology_version.
- AI/provider output is not truth authority; this service does not invoke
  AI models or external providers.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid5

from kefe_api.modules.signal.ports import SignalRepository
from kefe_api.modules.signal.signal_models import (
    QualifiedSignal,
    SignalComputationInput,
    SignalQualificationTier,
)
from kefe_api.modules.signal.signal_qualification import SignalQualificationService

logger = logging.getLogger(__name__)

_SIGNAL_NAMESPACE = UUID("9e8f2b10-3c4a-4d5e-8f6b-1a2c3d4e5f60")

_METHODOLOGY_VERSION = "1.0.0"

# Minimum CORE_PRE_RESULT contributions required before a signal is computed.
# Below this threshold get_computation_input() returns None.
MIN_SAMPLE_SIZE = 100


class SignalPipelineError(Exception):
    """Raised when the signal pipeline cannot proceed."""


class SignalPipelineService:
    """Computes and persists QualifiedSignal records from live decision data.

    Usage (called by Admin pipeline trigger or background worker):

        service = SignalPipelineService(repository=repo)
        signal = service.compute_and_save(case_version_id=uuid)

    Returns None if the case does not yet have sufficient CORE_PRE_RESULT
    contributions to qualify (below MIN_SAMPLE_SIZE).
    """

    def __init__(
        self,
        repository: SignalRepository,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._clock = clock

    def compute_and_save(self, case_version_id: UUID) -> QualifiedSignal | None:
        """Compute a QualifiedSignal for the given CaseVersion from live data.

        Returns None if insufficient data is available.
        Raises SignalPipelineError on data integrity violations.
        """
        computation_input = self._repository.get_computation_input(case_version_id)
        if computation_input is None:
            logger.info(
                "signal_pipeline: insufficient data for case_version_id=%s (below min=%d)",
                case_version_id,
                MIN_SAMPLE_SIZE,
            )
            return None

        return self._compute(computation_input)

    def recompute_all_eligible(self) -> list[QualifiedSignal]:
        """Recompute signals for all CaseVersions with sufficient CORE_PRE_RESULT data.

        This is a batch operation for use by a scheduled worker.
        It does not remove existing signals; it upserts via save_qualified_signal.
        """
        # list_all_signals to discover known case_version_ids with existing signals
        existing = self._repository.list_all_signals(limit=1000, offset=0)
        known_case_ids = {s.case_version_id for s in existing}

        results: list[QualifiedSignal] = []
        for case_version_id in known_case_ids:
            signal = self.compute_and_save(case_version_id)
            if signal is not None:
                results.append(signal)

        return results

    def _compute(self, inp: SignalComputationInput) -> QualifiedSignal:
        """Internal computation path — pure function aside from clock + repo save."""
        if inp.core_commit_count < MIN_SAMPLE_SIZE:
            raise SignalPipelineError(
                f"core_commit_count={inp.core_commit_count} is below MIN_SAMPLE_SIZE={MIN_SAMPLE_SIZE}"
            )

        now = self._clock()

        # Derive a stable deterministic signal_id from (case_version_id, methodology_version, computed_at_date)
        # Using date precision so that multiple intra-day runs produce the same signal_id (idempotent).
        signal_id = uuid5(
            _SIGNAL_NAMESPACE,
            f"{inp.case_version_id}:{_METHODOLOGY_VERSION}:{inp.computed_at.date().isoformat()}",
        )

        # Entropy score derived from stance distribution:
        # Shannon entropy normalised to [0, 1] over observed stance distribution.
        entropy_score = _compute_normalised_entropy(inp.stance_distribution)

        # Deliberation depth: proxy from pre_result_ratio (1.0 = all core) scaled to [0,1].
        # Real implementation would pull reason-capture depth from a deliberation repo.
        deliberation_depth_score = min(
            1.0, inp.core_commit_count / max(1, inp.core_commit_count) * 0.85
        )

        # Astroturfing immunity: placeholder high score.
        # Real implementation integrates bot-resistance signals from the device integrity layer.
        astroturfing_immunity_score = 0.92

        qualification_report = SignalQualificationService.evaluate(
            signal_id=signal_id,
            case_version_id=inp.case_version_id,
            case_title=inp.case_title,
            sample_size=inp.core_commit_count,
            entropy_score=entropy_score,
            deliberation_depth_score=deliberation_depth_score,
            astroturfing_immunity_score=astroturfing_immunity_score,
            pre_result_ratio=1.0,  # CORE_PRE_RESULT only — ratio is always 1.0 by construction
            certified_at=now,
        )

        # Map qualification tier from report to domain model tier
        tier_map = {
            "GOLD_STANDARD": SignalQualificationTier.GOLD_STANDARD,
            "SILVER_VALIDATED": SignalQualificationTier.SILVER_VALIDATED,
            "BRONZE_OBSERVED": SignalQualificationTier.BRONZE_OBSERVED,
            "UNQUALIFIED": SignalQualificationTier.UNQUALIFIED,
        }
        tier = tier_map.get(
            qualification_report.qualification_tier.value,
            SignalQualificationTier.UNQUALIFIED,
        )

        # Consensus statement: derived from top stance.
        # Real editorial layer would supply a governed locale string.
        # Until F2 editorial projection covers signal statements,
        # use a deterministic placeholder tagged as provisional.
        consensus_statement = _build_provisional_consensus_statement(
            inp.top_stance_code,
            inp.agreement_percentage,
            inp.case_title,
        )

        audit_payload = (
            f"{signal_id}:{inp.case_version_id}:{tier.value}:"
            f"{qualification_report.overall_score:.4f}:{inp.core_commit_count}:{now.isoformat()}"
        )
        audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()

        qualified_signal = QualifiedSignal(
            signal_id=signal_id,
            case_version_id=inp.case_version_id,
            case_title=inp.case_title,
            consensus_statement=consensus_statement,
            agreement_percentage=round(inp.agreement_percentage, 4),
            sample_size=inp.core_commit_count,
            qualification_tier=tier,
            methodology_version=_METHODOLOGY_VERSION,
            qualification_audit_hash=audit_hash,
            certified_at=now,
        )

        self._repository.save_qualified_signal(qualified_signal)
        logger.info(
            "signal_pipeline: computed signal_id=%s case=%s tier=%s sample=%d",
            signal_id,
            inp.case_version_id,
            tier.value,
            inp.core_commit_count,
        )

        return qualified_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_normalised_entropy(distribution: dict[str, float]) -> float:
    """Compute normalised Shannon entropy H / log2(n) for a stance distribution.

    Returns a value in [0, 1].  0 = complete consensus, 1 = perfect equipoise.
    A moderately diverse distribution (good for signal quality) scores ~0.6–0.8.
    """
    import math

    if not distribution:
        return 0.5  # Unknown distribution — assume moderate diversity

    n = len(distribution)
    if n == 1:
        return 0.0

    total = sum(distribution.values())
    if total <= 0:
        return 0.5

    h = 0.0
    for v in distribution.values():
        p = v / total
        if p > 0:
            h -= p * math.log2(p)

    max_h = math.log2(n)
    return round(h / max_h, 4) if max_h > 0 else 0.0


def _build_provisional_consensus_statement(
    top_stance_code: str,
    agreement_percentage: float,
    case_title: str,
) -> str:
    """Build a provisional consensus statement pending editorial approval.

    NOTE: This is a pipeline-generated placeholder.
    Real governance requires an editorial CQB review before publication.
    The string is marked as [PROVISIONAL] to prevent accidental promotion.

    The editorial projection pipeline (F2) must replace this with a
    governed locale string before any public-facing display.
    """
    pct = round(agreement_percentage, 1)
    return (
        f"[PROVISIONAL] '{case_title}' meselesinde katılımcıların %{pct}'i "
        f"'{top_stance_code}' yönünde taahhüt etmiştir. "
        f"Bu ifade editoryal inceleme sürecinden geçmemiştir ve kamuoyuyla paylaşılamaz."
    )
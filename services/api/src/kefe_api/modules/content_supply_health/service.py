from __future__ import annotations

from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthReason,
    ContentSupplyHealthSignal,
    ContentSupplyHealthSnapshot,
    ContentSupplyOperationalFacts,
)
from kefe_api.modules.content_supply_health.ports import (
    ContentSupplyOperationalFactsRepository,
)
from kefe_api.modules.ingestion_orchestration.models import utcnow

_NON_SUCCESS_CYCLE_STATES = frozenset({"DEGRADED", "FAILED", "ABANDONED"})


class ContentSupplyHealthService:
    def __init__(
        self,
        repository: ContentSupplyOperationalFactsRepository,
        *,
        clock=utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def snapshot(
        self,
        policy: ContentSupplyHealthPolicy,
        *,
        as_of=None,
    ) -> ContentSupplyHealthSnapshot:
        resolved_as_of = as_of or self._clock()
        facts = self._repository.read_facts(
            as_of=resolved_as_of,
            failure_window_seconds=policy.failure_window_seconds,
        )
        if facts.as_of != resolved_as_of:
            raise ValueError("operational facts as_of does not match requested snapshot")

        reasons = self._reason_codes(facts, policy)
        critical_reasons = {
            ContentSupplyHealthReason.STALE_SOURCE_DISPATCH.value,
            ContentSupplyHealthReason.STALE_INGESTION_LEASE.value,
            ContentSupplyHealthReason.STALE_CONTENT_SUPPLY_CYCLE.value,
        }
        if critical_reasons.intersection(reasons):
            signal = ContentSupplyHealthSignal.CRITICAL
        elif reasons:
            signal = ContentSupplyHealthSignal.ATTENTION
        elif self._is_quiet(facts):
            signal = ContentSupplyHealthSignal.QUIET
        else:
            signal = ContentSupplyHealthSignal.NOMINAL

        seconds_since_latest = None
        if facts.latest_terminal_cycle_completed_at is not None:
            seconds_since_latest = max(
                0,
                int(
                    (
                        facts.as_of - facts.latest_terminal_cycle_completed_at
                    ).total_seconds()
                ),
            )

        return ContentSupplyHealthSnapshot(
            signal=signal,
            as_of=facts.as_of,
            reason_codes=tuple(sorted(reasons)),
            active_schedule_count=facts.active_schedule_count,
            paused_schedule_count=facts.paused_schedule_count,
            due_schedule_count=facts.due_schedule_count,
            pending_dispatch_count=facts.pending_dispatch_count,
            running_dispatch_count=facts.running_dispatch_count,
            stale_dispatch_count=facts.stale_dispatch_count,
            recent_dispatch_non_success_count=(
                facts.recent_dispatch_non_success_count
            ),
            queued_ingestion_run_count=facts.queued_ingestion_run_count,
            running_ingestion_run_count=facts.running_ingestion_run_count,
            stale_ingestion_lease_count=facts.stale_ingestion_lease_count,
            recent_failed_ingestion_run_count=(
                facts.recent_failed_ingestion_run_count
            ),
            unreviewed_proposal_count=facts.unreviewed_proposal_count,
            running_cycle_count=facts.running_cycle_count,
            stale_cycle_count=facts.stale_cycle_count,
            recent_non_success_cycle_count=(
                facts.recent_non_success_cycle_count
            ),
            latest_terminal_cycle_state=facts.latest_terminal_cycle_state,
            latest_terminal_cycle_completed_at=(
                facts.latest_terminal_cycle_completed_at
            ),
            seconds_since_latest_terminal_cycle=seconds_since_latest,
        )

    @staticmethod
    def _reason_codes(
        facts: ContentSupplyOperationalFacts,
        policy: ContentSupplyHealthPolicy,
    ) -> set[str]:
        reasons: set[str] = set()
        if facts.stale_dispatch_count > 0:
            reasons.add(ContentSupplyHealthReason.STALE_SOURCE_DISPATCH.value)
        if facts.stale_ingestion_lease_count > 0:
            reasons.add(ContentSupplyHealthReason.STALE_INGESTION_LEASE.value)
        if facts.stale_cycle_count > 0:
            reasons.add(ContentSupplyHealthReason.STALE_CONTENT_SUPPLY_CYCLE.value)

        if (
            facts.pending_dispatch_count
            > policy.pending_dispatch_attention_threshold
        ):
            reasons.add(ContentSupplyHealthReason.SOURCE_DISPATCH_BACKLOG.value)
        if facts.queued_ingestion_run_count > policy.queued_run_attention_threshold:
            reasons.add(ContentSupplyHealthReason.INGESTION_RUN_BACKLOG.value)
        if (
            facts.unreviewed_proposal_count
            > policy.unreviewed_proposal_attention_threshold
        ):
            reasons.add(ContentSupplyHealthReason.PROPOSAL_REVIEW_BACKLOG.value)

        threshold = policy.recent_non_success_attention_threshold
        if facts.recent_dispatch_non_success_count > threshold:
            reasons.add(
                ContentSupplyHealthReason.RECENT_SOURCE_DISPATCH_NON_SUCCESS.value
            )
        if facts.recent_failed_ingestion_run_count > threshold:
            reasons.add(ContentSupplyHealthReason.RECENT_INGESTION_FAILURE.value)
        if facts.recent_non_success_cycle_count > threshold:
            reasons.add(
                ContentSupplyHealthReason.RECENT_CONTENT_SUPPLY_CYCLE_NON_SUCCESS.value
            )
        if facts.latest_terminal_cycle_state in _NON_SUCCESS_CYCLE_STATES:
            reasons.add(
                ContentSupplyHealthReason.LATEST_CONTENT_SUPPLY_CYCLE_NON_SUCCESS.value
            )

        latest = facts.latest_terminal_cycle_completed_at
        cycle_is_silent = (
            facts.active_schedule_count > 0
            and facts.running_cycle_count == 0
            and (
                latest is None
                or (facts.as_of - latest).total_seconds()
                > policy.max_cycle_silence_seconds
            )
        )
        if cycle_is_silent:
            reasons.add(ContentSupplyHealthReason.CONTENT_SUPPLY_CYCLE_SILENT.value)
        return reasons

    @staticmethod
    def _is_quiet(facts: ContentSupplyOperationalFacts) -> bool:
        return (
            facts.active_schedule_count == 0
            and facts.due_schedule_count == 0
            and facts.pending_dispatch_count == 0
            and facts.running_dispatch_count == 0
            and facts.queued_ingestion_run_count == 0
            and facts.running_ingestion_run_count == 0
            and facts.unreviewed_proposal_count == 0
            and facts.running_cycle_count == 0
        )

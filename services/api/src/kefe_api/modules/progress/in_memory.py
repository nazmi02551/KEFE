from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.progress.models import (
    DecisionJourneySnapshot,
    DomainActivity,
    ProgressSnapshot,
    RecentCompletedCase,
    RecentDecisionJourney,
)


class InMemoryProgressRepository:
    def __init__(self, decision_repository: InMemoryDecisionRepository) -> None:
        self._decision_repository = decision_repository

    def get_progress(self, actor_id: UUID, *, recent_limit: int) -> ProgressSnapshot:
        sessions = self._committed_sessions(actor_id)
        recent: list[RecentCompletedCase] = []
        domains: set[str] = set()
        case_ids: set[UUID] = set()
        committed_times = [session.committed_at for session in sessions if session.committed_at]

        for session in sessions:
            case = self._decision_repository.get_case_version(session.case_version_id)
            if case is None or session.committed_at is None:
                continue
            domains.add(case.primary_domain)
            case_ids.add(case.case_id)
            if len(recent) < recent_limit:
                recent.append(
                    RecentCompletedCase(
                        case_id=case.case_id,
                        case_version_id=case.id,
                        title=case.title,
                        primary_domain=case.primary_domain,
                        committed_at=session.committed_at,
                    )
                )

        return ProgressSnapshot(
            actor_id=actor_id,
            meaningful_weigh_count=len(sessions),
            distinct_case_count=len(case_ids),
            distinct_domain_count=len(domains),
            first_committed_at=min(committed_times) if committed_times else None,
            last_committed_at=max(committed_times) if committed_times else None,
            recent_cases=tuple(recent),
        )

    def get_journey(
        self,
        actor_id: UUID,
        *,
        recent_limit: int,
        domain_limit: int,
    ) -> DecisionJourneySnapshot:
        sessions = self._committed_sessions(actor_id)
        if not sessions:
            return DecisionJourneySnapshot.empty(actor_id)

        list_revisions = getattr(self._decision_repository, "list_decision_revisions", None)
        list_reflections = getattr(self._decision_repository, "list_reflection_completions", None)

        decision_update_count = 0
        revisited_case_count = 0
        reflection_completion_count = 0
        domain_counts: dict[str, int] = defaultdict(int)
        domain_last: dict[str, datetime] = {}
        recent: list[RecentDecisionJourney] = []

        for session in sessions:
            case = self._decision_repository.get_case_version(session.case_version_id)
            if case is None or session.committed_at is None:
                continue

            domain_counts[case.primary_domain] += 1
            previous_last = domain_last.get(case.primary_domain)
            if previous_last is None or session.committed_at > previous_last:
                domain_last[case.primary_domain] = session.committed_at

            revisions = tuple(list_revisions(session.id)) if list_revisions else ()
            later_revisions = tuple(item for item in revisions if item.revision_no > 1)
            update_count = len(later_revisions)
            decision_update_count += update_count
            if update_count:
                revisited_case_count += 1

            completions = tuple(list_reflections(session.id)) if list_reflections else ()
            reflection_completion_count += len(completions)
            latest_decision_at = max(
                (item.committed_at for item in later_revisions),
                default=session.committed_at,
            )

            if len(recent) < recent_limit:
                recent.append(
                    RecentDecisionJourney(
                        case_id=case.case_id,
                        case_version_id=case.id,
                        title=case.title,
                        primary_domain=case.primary_domain,
                        initial_committed_at=session.committed_at,
                        latest_decision_at=latest_decision_at,
                        decision_update_count=update_count,
                        reflection_completed=bool(completions),
                    )
                )

        domain_activity = tuple(
            DomainActivity(
                primary_domain=domain,
                committed_weigh_count=count,
                last_committed_at=domain_last[domain],
            )
            for domain, count in sorted(
                domain_counts.items(),
                key=lambda item: (-item[1], -domain_last[item[0]].timestamp(), item[0]),
            )[:domain_limit]
        )

        return DecisionJourneySnapshot(
            actor_id=actor_id,
            decision_update_count=decision_update_count,
            revisited_case_count=revisited_case_count,
            reflection_completion_count=reflection_completion_count,
            domain_activity=domain_activity,
            recent_journeys=tuple(recent),
        )

    def _committed_sessions(self, actor_id: UUID):
        return sorted(
            self._decision_repository.list_actor_committed_sessions(actor_id),
            key=lambda item: (item.committed_at or item.started_at, str(item.id)),
            reverse=True,
        )

from __future__ import annotations

from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.progress.models import ProgressSnapshot, RecentCompletedCase


class InMemoryProgressRepository:
    def __init__(self, decision_repository: InMemoryDecisionRepository) -> None:
        self._decision_repository = decision_repository

    def get_progress(self, actor_id: UUID, *, recent_limit: int) -> ProgressSnapshot:
        sessions = self._decision_repository.list_actor_committed_sessions(actor_id)
        sessions = sorted(
            sessions,
            key=lambda item: item.committed_at or item.started_at,
            reverse=True,
        )
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

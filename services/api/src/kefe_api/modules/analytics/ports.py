from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.analytics.models import (
    ActivationJourney,
    AnalyticsEvent,
    QualityJourney,
)


class AnalyticsEventStore(Protocol):
    def append_once(self, event: AnalyticsEvent) -> bool: ...

    def get(self, event_id: UUID) -> AnalyticsEvent | None: ...

    def list_by_source_event(self, source_event_id: UUID) -> tuple[AnalyticsEvent, ...]: ...

    def list_by_session(self, session_id: UUID) -> tuple[AnalyticsEvent, ...]: ...

    def get_activation_journey(self, session_id: UUID) -> ActivationJourney | None: ...

    def get_quality_journey(self, session_id: UUID) -> QualityJourney | None: ...


class AnalyticsActorAnonymizer(Protocol):
    def anonymize_actor(self, actor_id: UUID) -> tuple[int, int]: ...

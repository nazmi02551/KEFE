from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.analytics.models import AnalyticsEvent


class AnalyticsEventStore(Protocol):
    def append_once(self, event: AnalyticsEvent) -> bool: ...

    def get(self, event_id: UUID) -> AnalyticsEvent | None: ...

    def list_by_source_event(self, source_event_id: UUID) -> tuple[AnalyticsEvent, ...]: ...

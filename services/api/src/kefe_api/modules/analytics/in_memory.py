from __future__ import annotations

from copy import deepcopy
from threading import RLock
from uuid import UUID

from kefe_api.modules.analytics.models import AnalyticsEvent


class InMemoryAnalyticsEventStore:
    def __init__(self) -> None:
        self._events: dict[UUID, AnalyticsEvent] = {}
        self._by_source: dict[UUID, list[UUID]] = {}
        self._lock = RLock()

    def append_once(self, event: AnalyticsEvent) -> bool:
        with self._lock:
            if event.id in self._events:
                return False
            self._events[event.id] = deepcopy(event)
            self._by_source.setdefault(event.source_event_id, []).append(event.id)
            return True

    def get(self, event_id: UUID) -> AnalyticsEvent | None:
        with self._lock:
            event = self._events.get(event_id)
            return deepcopy(event) if event is not None else None

    def list_by_source_event(self, source_event_id: UUID) -> tuple[AnalyticsEvent, ...]:
        with self._lock:
            return tuple(
                deepcopy(self._events[event_id])
                for event_id in self._by_source.get(source_event_id, ())
            )

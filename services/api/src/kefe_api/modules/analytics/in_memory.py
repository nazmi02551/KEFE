from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from threading import RLock
from uuid import UUID

from kefe_api.modules.analytics.models import ActivationJourney, AnalyticsEvent
from kefe_api.modules.analytics.service import ActivationJourneyProjector


class InMemoryAnalyticsEventStore:
    def __init__(self) -> None:
        self._events: dict[UUID, AnalyticsEvent] = {}
        self._by_source: dict[UUID, list[UUID]] = {}
        self._by_session: dict[UUID, list[UUID]] = {}
        self._journeys: dict[UUID, ActivationJourney] = {}
        self._journey_projector = ActivationJourneyProjector()
        self._lock = RLock()

    def append_once(self, event: AnalyticsEvent) -> bool:
        with self._lock:
            if event.id in self._events:
                return False
            next_journey = self._journey_projector.apply(
                self._journeys.get(event.session_id),
                event,
            )
            self._events[event.id] = deepcopy(event)
            self._by_source.setdefault(event.source_event_id, []).append(event.id)
            self._by_session.setdefault(event.session_id, []).append(event.id)
            if next_journey is not None:
                self._journeys[event.session_id] = deepcopy(next_journey)
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

    def list_by_session(self, session_id: UUID) -> tuple[AnalyticsEvent, ...]:
        with self._lock:
            return tuple(
                deepcopy(self._events[event_id])
                for event_id in self._by_session.get(session_id, ())
            )

    def get_activation_journey(self, session_id: UUID) -> ActivationJourney | None:
        with self._lock:
            journey = self._journeys.get(session_id)
            return deepcopy(journey) if journey is not None else None

    def anonymize_actor(self, actor_id: UUID) -> tuple[int, int]:
        with self._lock:
            event_count = 0
            for event_id, event in tuple(self._events.items()):
                if event.actor_id == actor_id:
                    self._events[event_id] = replace(event, actor_id=None)
                    event_count += 1

            journey_count = 0
            for session_id, journey in tuple(self._journeys.items()):
                if journey.actor_id == actor_id:
                    self._journeys[session_id] = replace(journey, actor_id=None)
                    journey_count += 1
            return event_count, journey_count

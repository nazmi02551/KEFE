from __future__ import annotations

from kefe_api.modules.analytics.ports import AnalyticsEventStore
from kefe_api.modules.analytics.service import AnalyticsEventProjector
from kefe_api.modules.events.models import OutboxEvent


class AnalyticsProjectionTransport:
    def __init__(
        self,
        *,
        projector: AnalyticsEventProjector,
        store: AnalyticsEventStore,
    ) -> None:
        self._projector = projector
        self._store = store

    def publish(self, event: OutboxEvent) -> None:
        projected = self._projector.project(event)
        if projected is not None:
            self._store.append_once(projected)

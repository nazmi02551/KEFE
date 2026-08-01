from __future__ import annotations

import json
import logging

from kefe_api.modules.events.models import OutboxEvent
from kefe_api.modules.events.ports import EventTransport

logger = logging.getLogger("kefe.events")


class CompositeEventTransport:
    def __init__(self, transports: tuple[EventTransport, ...]) -> None:
        if not transports:
            raise ValueError("at least one event transport is required")
        self._transports = transports

    def publish(self, event: OutboxEvent) -> None:
        for transport in self._transports:
            transport.publish(event)


class LoggingEventTransport:
    """Development transport; replaceable by queue/broker adapters."""

    def publish(self, event: OutboxEvent) -> None:
        logger.info(
            "domain_event %s",
            json.dumps(
                {
                    "event_id": str(event.id),
                    "event_name": event.event_name,
                    "event_version": event.event_version,
                    "aggregate_type": event.aggregate_type,
                    "aggregate_id": str(event.aggregate_id),
                    "occurred_at": event.occurred_at.isoformat(),
                    "payload": event.payload,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

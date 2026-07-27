from __future__ import annotations

import logging
import signal
import time

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.event_transports import LoggingEventTransport
from kefe_api.infrastructure.postgres_outbox import PostgresOutboxStore
from kefe_api.modules.events.service import OutboxPublisher, RetryPolicy

logger = logging.getLogger("kefe.outbox")


class StopFlag:
    def __init__(self) -> None:
        self.requested = False

    def request(self, *_args: object) -> None:
        self.requested = True


def build_publisher() -> OutboxPublisher:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required for the outbox worker")

    if settings.event_transport != "logging":
        raise RuntimeError(f"Unsupported event transport: {settings.event_transport}")

    engine = build_engine(settings.database_url)
    return OutboxPublisher(
        store=PostgresOutboxStore(engine),
        transport=LoggingEventTransport(),
        retry_policy=RetryPolicy(
            base_seconds=settings.outbox_retry_base_seconds,
            max_seconds=settings.outbox_retry_max_seconds,
            max_attempts=settings.outbox_max_attempts,
        ),
        batch_size=settings.outbox_batch_size,
        lease_seconds=settings.outbox_lease_seconds,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    stop = StopFlag()
    signal.signal(signal.SIGINT, stop.request)
    signal.signal(signal.SIGTERM, stop.request)
    publisher = build_publisher()

    logger.info("KEFE outbox worker started")
    while not stop.requested:
        result = publisher.run_once()
        if result.claimed == 0:
            time.sleep(settings.outbox_poll_seconds)
            continue
        logger.info(
            "outbox batch claimed=%s published=%s failed=%s dead_lettered=%s",
            result.claimed,
            result.published,
            result.failed,
            result.dead_lettered,
        )
    logger.info("KEFE outbox worker stopped")


if __name__ == "__main__":
    main()

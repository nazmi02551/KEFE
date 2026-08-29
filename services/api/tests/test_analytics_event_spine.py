from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from kefe_api.infrastructure.event_transports import CompositeEventTransport
from kefe_api.modules.analytics.in_memory import InMemoryAnalyticsEventStore
from kefe_api.modules.analytics.registry import default_analytics_registry
from kefe_api.modules.analytics.service import (
    AnalyticsEventProjector,
    AnalyticsProjectionError,
)
from kefe_api.modules.analytics.transport import AnalyticsProjectionTransport
from kefe_api.modules.events.models import OutboxEvent


def _projector() -> AnalyticsEventProjector:
    return AnalyticsEventProjector(
        registry=default_analytics_registry(),
        producer_version="0.19.0-test",
    )


def _source(
    name: str,
    payload: dict[str, object],
    *,
    event_id: UUID | None = None,
    aggregate_id: UUID | None = None,
) -> OutboxEvent:
    return OutboxEvent(
        id=event_id or uuid4(),
        aggregate_type="weigh_session",
        aggregate_id=aggregate_id or uuid4(),
        event_name=name,
        event_version=1,
        occurred_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        payload=payload,
        attempts=1,
    )


def test_unknown_source_event_is_ignored() -> None:
    assert _projector().project(_source("unknown.event", {})) is None


def test_unknown_source_event_still_reaches_external_transport() -> None:
    source = _source("content.unregistered", {"safe": True})
    store = InMemoryAnalyticsEventStore()
    analytics = AnalyticsProjectionTransport(projector=_projector(), store=store)

    class Recorder:
        def __init__(self) -> None:
            self.events: list[OutboxEvent] = []

        def publish(self, event: OutboxEvent) -> None:
            self.events.append(event)

    recorder = Recorder()
    CompositeEventTransport((analytics, recorder)).publish(source)

    assert recorder.events == [source]
    assert store.list_by_source_event(source.id) == ()


def test_weigh_start_extracts_typed_provenance() -> None:
    actor_id = uuid4()
    case_version_id = uuid4()
    session_id = uuid4()
    projected = _projector().project(
        _source(
            "weigh.started",
            {
                "actor_id": str(actor_id),
                "case_version_id": str(case_version_id),
                "unregistered_field": "ignored",
            },
            aggregate_id=session_id,
        )
    )

    assert projected is not None
    assert projected.analytics_name == "activation.weigh_started"
    assert projected.actor_id == actor_id
    assert projected.session_id == session_id
    assert projected.case_version_id == case_version_id
    assert projected.payload == {}


def test_commit_keeps_only_allowlisted_facts() -> None:
    projected = _projector().project(
        _source(
            "weigh.committed",
            {
                "actor_id": str(uuid4()),
                "case_version_id": str(uuid4()),
                "committed_at": "2026-08-01T12:00:00+00:00",
                "has_reason": True,
                "internal_debug": "not copied",
            },
        )
    )

    assert projected is not None
    assert projected.contribution_class == "CORE_PRE_RESULT"
    assert projected.payload == {
        "committed_at": "2026-08-01T12:00:00+00:00",
        "has_reason": True,
    }
    assert projected.metric_families == ("ACTIVATION", "QUALITY")


def test_forbidden_nested_payload_key_fails_closed() -> None:
    with pytest.raises(AnalyticsProjectionError, match="reason_text"):
        _projector().project(
            _source(
                "weigh.committed",
                {
                    "actor_id": str(uuid4()),
                    "case_version_id": str(uuid4()),
                    "has_reason": True,
                    "nested": {"reason_text": "must not reach analytics"},
                },
            )
        )


def test_required_provenance_is_not_guessed() -> None:
    with pytest.raises(AnalyticsProjectionError, match="actor_id"):
        _projector().project(
            _source(
                "weigh.started",
                {"case_version_id": str(uuid4())},
            )
        )


def test_projection_identity_and_store_are_idempotent() -> None:
    source = _source(
        "result.revealed",
        {"case_version_id": str(uuid4()), "layer": "TRUSTED"},
    )
    first = _projector().project(source)
    second = _projector().project(source)
    assert first is not None and second is not None
    assert first.id == second.id

    store = InMemoryAnalyticsEventStore()
    assert store.append_once(first) is True
    assert store.append_once(second) is False
    assert store.list_by_source_event(source.id) == (first,)


def test_composite_retry_does_not_duplicate_analytics() -> None:
    source = _source(
        "perspective.viewed",
        {
            "case_version_id": str(uuid4()),
            "mode": "CURATED",
            "card_count": 3,
        },
    )
    store = InMemoryAnalyticsEventStore()
    analytics = AnalyticsProjectionTransport(projector=_projector(), store=store)

    class Recorder:
        def __init__(self) -> None:
            self.count = 0

        def publish(self, event: OutboxEvent) -> None:
            assert event.id == source.id
            self.count += 1

    recorder = Recorder()
    composite = CompositeEventTransport((analytics, recorder))
    composite.publish(source)
    composite.publish(source)

    assert recorder.count == 2
    assert len(store.list_by_source_event(source.id)) == 1

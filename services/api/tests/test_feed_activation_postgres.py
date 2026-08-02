from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_feed_activation import (
    PostgresFeedPipelineDefinitionRepository,
)
from kefe_api.modules.knowledge.feed_activation import (
    FeedPipelineDefinition,
    FeedPipelineLifecycle,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _definition(feed_code: str, base: datetime) -> FeedPipelineDefinition:
    return FeedPipelineDefinition.create(
        feed_code=feed_code,
        adapter_code="provider.pg_feed.v1",
        external_locator="https://feeds.example.test/postgres.xml",
        adoption_configuration_hash="sha256:" + "a" * 64,
        parser_configuration_hash="sha256:" + "b" * 64,
        extraction_pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        extraction_pipeline_version="1.0.0",
        acquisition_configuration_hash="sha256:" + "c" * 64,
        interval_seconds=300,
        max_dispatch_attempts=3,
        evidence_capability_ref="evidence://capability/postgres-feed-v1",
        created_at=base,
    )


def _cleanup(engine, *feed_codes: str) -> None:
    with engine.begin() as connection:
        for feed_code in feed_codes:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.feed_pipeline_definition
                    WHERE feed_code = :feed_code
                    """
                ),
                {"feed_code": feed_code},
            )


def test_postgres_create_or_get_is_immutable_and_transitions_are_durable() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    feed_code = f"feed.pg_{uuid4().hex[:10]}.v1"
    repository = PostgresFeedPipelineDefinitionRepository(engine)
    try:
        created = repository.create_or_get(_definition(feed_code, base))
        assert created.lifecycle_state is FeedPipelineLifecycle.DRAFT
        same = repository.create_or_get(_definition(feed_code, base))
        assert same == created
        changed = FeedPipelineDefinition.create(
            feed_code=feed_code,
            adapter_code=created.adapter_code,
            external_locator=created.external_locator,
            adoption_configuration_hash=created.adoption_configuration_hash,
            parser_configuration_hash=created.parser_configuration_hash,
            extraction_pipeline_code=created.extraction_pipeline_code,
            extraction_pipeline_version=created.extraction_pipeline_version,
            acquisition_configuration_hash=created.acquisition_configuration_hash,
            interval_seconds=600,
            max_dispatch_attempts=created.max_dispatch_attempts,
            evidence_capability_ref=created.evidence_capability_ref,
            created_at=base,
        )
        with pytest.raises(ValueError, match="immutable"):
            repository.create_or_get(changed)

        fingerprint = "sha256:" + "d" * 64
        enabled = repository.transition(
            feed_code=feed_code,
            target=FeedPipelineLifecycle.ENABLED,
            at=base + timedelta(seconds=1),
            dependency_fingerprint=fingerprint,
        )
        paused = repository.transition(
            feed_code=feed_code,
            target=FeedPipelineLifecycle.PAUSED,
            at=base + timedelta(seconds=2),
        )
        retired = repository.transition(
            feed_code=feed_code,
            target=FeedPipelineLifecycle.RETIRED,
            at=base + timedelta(seconds=3),
        )
        assert enabled.dependency_fingerprint == fingerprint
        assert paused.lifecycle_state is FeedPipelineLifecycle.PAUSED
        assert retired.lifecycle_state is FeedPipelineLifecycle.RETIRED
        stored = repository.get(feed_code)
        assert stored is not None
        assert stored.lifecycle_state is FeedPipelineLifecycle.RETIRED
        assert stored.dependency_fingerprint == fingerprint
        assert stored.verified_at == base + timedelta(seconds=1)
    finally:
        _cleanup(engine, feed_code)


def test_postgres_concurrent_enable_uses_row_lock_and_exactly_one_transition() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    feed_code = f"feed.pg_concurrent_{uuid4().hex[:8]}.v1"
    repository = PostgresFeedPipelineDefinitionRepository(engine)
    fingerprint = "sha256:" + "e" * 64
    try:
        repository.create_or_get(_definition(feed_code, base))
        barrier = Barrier(2)

        def enable_once(index: int) -> str:
            local = PostgresFeedPipelineDefinitionRepository(engine)
            barrier.wait()
            try:
                local.transition(
                    feed_code=feed_code,
                    target=FeedPipelineLifecycle.ENABLED,
                    at=base + timedelta(seconds=index + 1),
                    dependency_fingerprint=fingerprint,
                )
            except ValueError:
                return "BLOCKED"
            return "ENABLED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(enable_once, range(2)))

        assert sorted(results) == ["BLOCKED", "ENABLED"]
        stored = repository.get(feed_code)
        assert stored is not None
        assert stored.lifecycle_state is FeedPipelineLifecycle.ENABLED
        assert stored.dependency_fingerprint == fingerprint
    finally:
        _cleanup(engine, feed_code)


def test_postgres_feed_activation_constraints_reject_invalid_cross_fields() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    feed_code = f"feed.pg_constraint_{uuid4().hex[:8]}.v1"
    repository = PostgresFeedPipelineDefinitionRepository(engine)
    try:
        repository.create_or_get(_definition(feed_code, base))
        with pytest.raises(Exception):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.feed_pipeline_definition
                        SET dependency_fingerprint = :fingerprint,
                            verified_at = NULL
                        WHERE feed_code = :feed_code
                        """
                    ),
                    {
                        "feed_code": feed_code,
                        "fingerprint": "sha256:" + "f" * 64,
                    },
                )
        with engine.connect() as connection:
            state = connection.execute(
                text(
                    """
                    SELECT lifecycle_state, dependency_fingerprint, verified_at
                    FROM knowledge.feed_pipeline_definition
                    WHERE feed_code = :feed_code
                    """
                ),
                {"feed_code": feed_code},
            ).mappings().one()
        assert state["lifecycle_state"] == "DRAFT"
        assert state["dependency_fingerprint"] is None
        assert state["verified_at"] is None
    finally:
        _cleanup(engine, feed_code)

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.infrastructure.postgres_canonical_public_feed_catalog import (
    PostgresCanonicalPublicFeedCatalogRepository,
)
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedDefinition,
    PublicFeedActivationProjection,
    PublicFeedActivationState,
    PublicFeedAuditAction,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

NOW = datetime(2026, 8, 4, 13, 0, tzinfo=UTC)


def _definition(feed_code: str, version: int) -> CanonicalPublicFeedDefinition:
    public = PublicFeedDefinition(
        feed_code=feed_code,
        display_name="Canonical PostgreSQL Feed",
        adapter_code=f"kefe.public_feed.{feed_code}.v{version}",
        external_locator=f"https://feeds.example.test/{feed_code}.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1500,
        read_timeout_ms=3000,
        total_timeout_ms=5000,
        max_response_bytes=2_000_000,
        max_redirect_hops=2,
        terms_evidence_ref=f"evidence://provider-terms/{feed_code}/v1",
        rate_limit_evidence_ref=f"evidence://provider-rate/{feed_code}/v1",
        quota_limit=12,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=120,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )
    return CanonicalPublicFeedDefinition.create(
        definition_version=version,
        definition=public,
        interval_seconds=900,
        max_dispatch_attempts=4,
        created_at=NOW,
        created_by_actor_ref="admin:creator",
    )


def test_postgres_catalog_is_durable_idempotent_and_append_only() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    feed_code = f"postgres-{uuid4().hex[:12]}"
    draft = _definition(feed_code, 1)

    def register_once() -> CanonicalPublicFeedDefinition:
        local = PostgresCanonicalPublicFeedCatalogRepository(
            create_engine(database_url)
        )
        return local.add_definition(draft)

    with ThreadPoolExecutor(max_workers=2) as executor:
        registered = tuple(executor.map(lambda _index: register_once(), range(2)))
    assert registered == (draft, draft)

    restarted = PostgresCanonicalPublicFeedCatalogRepository(
        create_engine(database_url)
    )
    assert restarted.get_definition(feed_code, 1) == draft
    assert restarted.get_latest(feed_code) == draft

    preflighted = draft.mark_preflight(actor_ref="admin:creator", at=NOW)
    assert restarted.replace_definition(preflighted) == preflighted
    approved = preflighted.approve(actor_ref="admin:approver", at=NOW)
    assert restarted.replace_definition(approved) == approved
    assert (
        restarted.get_definition(feed_code, 1).state
        is PublicFeedCatalogState.APPROVED
    )

    activation = PublicFeedActivationProjection.create(
        definition=approved,
        schedule_id=uuid4(),
        actor_ref="admin:activator",
        at=NOW,
    )
    assert restarted.add_activation(activation) == activation
    assert restarted.add_activation(activation) == activation
    paused = activation.transition(
        PublicFeedActivationState.PAUSED,
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=1),
    )
    assert restarted.replace_activation(paused) == paused
    assert restarted.get_activation_for_definition(approved.id) == paused

    event = restarted.append_audit(
        definition_id=approved.id,
        activation_id=paused.id,
        action=PublicFeedAuditAction.PAUSED,
        actor_ref="admin:activator",
        occurred_at=NOW + timedelta(seconds=1),
        configuration_hash=approved.configuration_hash,
    )
    assert restarted.list_audit(approved.id) == (event,)

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_audit
                    SET action = 'RESUMED'
                    WHERE sequence = :sequence
                    """
                ),
                {"sequence": event.sequence},
            )

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_definition
                    SET adapter_code = :adapter_code
                    WHERE id = :definition_id
                    """
                ),
                {
                    "definition_id": approved.id,
                    "adapter_code": f"kefe.public_feed.{feed_code}.v999",
                },
            )


def test_postgres_catalog_rejects_conflicting_same_version() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    repository = PostgresCanonicalPublicFeedCatalogRepository(
        create_engine(database_url)
    )
    feed_code = f"conflict-{uuid4().hex[:12]}"
    original = _definition(feed_code, 1)
    repository.add_definition(original)

    conflicting_public = PublicFeedDefinition(
        feed_code=feed_code,
        display_name="Conflicting Feed",
        adapter_code=f"kefe.public_feed.{feed_code}.v1",
        external_locator=f"https://feeds.example.test/{feed_code}-other.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1500,
        read_timeout_ms=3000,
        total_timeout_ms=5000,
        max_response_bytes=2_000_000,
        max_redirect_hops=2,
        terms_evidence_ref=f"evidence://provider-terms/{feed_code}/v2",
        rate_limit_evidence_ref=f"evidence://provider-rate/{feed_code}/v2",
        quota_limit=12,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=120,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )
    conflicting = CanonicalPublicFeedDefinition.create(
        definition_version=1,
        definition=conflicting_public,
        interval_seconds=900,
        max_dispatch_attempts=4,
        created_at=NOW,
        created_by_actor_ref="admin:creator",
    )
    with pytest.raises(ValueError, match="identity conflict"):
        repository.add_definition(conflicting)

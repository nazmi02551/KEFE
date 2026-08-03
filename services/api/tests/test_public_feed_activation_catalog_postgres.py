from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.infrastructure.postgres_public_feed_activation_catalog import (
    PostgresPublicFeedActivationCatalogRepository,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ProviderAdoptionProfile,
    ProviderHttpMethod,
)
from kefe_api.modules.knowledge.public_feed_activation import (
    PublicFeedActivationDefinition,
)
from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    PublicFeedActivationCatalogEntry,
)
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _definition(identity: str) -> PublicFeedActivationDefinition:
    adapter_code = f"test.pg_catalog_feed_{identity}.v1"
    activation_code = f"test.pg_catalog_activation_{identity}.v1"
    parser = StrictRssAtomParseProfile(
        max_document_bytes=4096,
        max_items=32,
    )
    now = datetime.now(UTC).replace(microsecond=0)
    capability = SourceProviderCapability.create(
        adapter_code=adapter_code,
        credential_mode=ProviderCredentialMode.PUBLIC,
        secret_ref=None,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        created_at=now,
    )
    adoption = ProviderAdoptionProfile(
        adapter_code=adapter_code,
        allowed_origins=(f"https://feeds-{identity}.example.test",),
        allowed_methods=(ProviderHttpMethod.GET,),
        allowed_media_types=parser.accepted_media_types,
        connect_timeout_ms=200,
        read_timeout_ms=500,
        total_timeout_ms=1000,
        max_response_bytes=parser.max_document_bytes,
        max_redirect_hops=1,
        terms_evidence_ref=f"docref://pg-catalog/{identity}/terms-v1",
        rate_limit_evidence_ref=f"evidence://pg-catalog/{identity}/rate-v1",
    )
    return PublicFeedActivationDefinition(
        activation_code=activation_code,
        adapter_code=adapter_code,
        external_locator=f"https://feeds-{identity}.example.test/news.xml",
        adoption_profile=adoption,
        parser_profile=parser,
        capability=capability,
        first_due_at=now,
        interval_seconds=300,
        max_dispatch_attempts=3,
        locale="en",
        jurisdiction_code="GLOBAL",
    )


def _entry(identity: str) -> PublicFeedActivationCatalogEntry:
    return PublicFeedActivationCatalogEntry.from_definition(
        _definition(identity),
        evidence_ref=f"evidence://pg-catalog/{identity}/review-v1",
        recorded_by=f"admin:{uuid4()}",
        recorded_at=datetime.now(UTC).replace(microsecond=0),
    )


def test_postgres_catalog_is_idempotent_and_survives_repository_restart() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresPublicFeedActivationCatalogRepository(engine)
    identity = uuid4().hex[:10]
    first = _entry(identity)

    stored = repository.create_or_get(first)
    rerecorded = PublicFeedActivationCatalogEntry.from_definition(
        _definition(identity),
        evidence_ref=first.evidence_ref,
        recorded_by=f"admin:{uuid4()}",
        recorded_at=first.recorded_at + timedelta(minutes=5),
    )
    assert repository.create_or_get(rerecorded) == stored

    restarted = PostgresPublicFeedActivationCatalogRepository(engine)
    assert restarted.get_by_activation_code(first.activation_code) == stored
    assert restarted.get_by_adapter_code(first.adapter_code) == stored
    assert stored in restarted.list_entries(limit=100)
    assert restarted.get_by_activation_code(first.activation_code).manifest_payload() == (
        first.manifest_payload()
    )


def test_postgres_catalog_conflicts_fail_closed() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresPublicFeedActivationCatalogRepository(engine)
    identity = uuid4().hex[:10]
    first = repository.create_or_get(_entry(identity))

    changed_definition = _definition(identity)
    changed_definition = PublicFeedActivationDefinition(
        activation_code=changed_definition.activation_code,
        adapter_code=changed_definition.adapter_code,
        external_locator=changed_definition.external_locator,
        adoption_profile=changed_definition.adoption_profile,
        parser_profile=changed_definition.parser_profile,
        capability=changed_definition.capability,
        first_due_at=changed_definition.first_due_at,
        interval_seconds=600,
        max_dispatch_attempts=changed_definition.max_dispatch_attempts,
        locale=changed_definition.locale,
        jurisdiction_code=changed_definition.jurisdiction_code,
    )
    conflict = PublicFeedActivationCatalogEntry.from_definition(
        changed_definition,
        evidence_ref=first.evidence_ref,
        recorded_by=f"admin:{uuid4()}",
        recorded_at=first.recorded_at,
    )
    with pytest.raises(ValueError, match="conflicting"):
        repository.create_or_get(conflict)


def test_postgres_catalog_table_rejects_update_and_delete() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    entry = PostgresPublicFeedActivationCatalogRepository(engine).create_or_get(
        _entry(uuid4().hex[:10])
    )

    for statement in (
        """
        UPDATE knowledge.public_feed_activation_catalog
        SET evidence_ref = 'evidence://forbidden/change-v1'
        WHERE id = :entry_id
        """,
        """
        DELETE FROM knowledge.public_feed_activation_catalog
        WHERE id = :entry_id
        """,
    ):
        with pytest.raises(DBAPIError) as caught:
            with engine.begin() as connection:
                connection.execute(text(statement), {"entry_id": entry.id})
        assert "public feed activation catalog is immutable" in str(
            caught.value.orig
        )


def test_postgres_repository_revalidates_manifest_hash_on_read() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    identity = uuid4().hex[:10]
    entry = _entry(identity)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO knowledge.public_feed_activation_catalog (
                    id, activation_code, adapter_code, configuration_hash,
                    manifest_schema_version, manifest_json, evidence_ref,
                    recorded_by, recorded_at
                ) VALUES (
                    :id, :activation_code, :adapter_code, :configuration_hash,
                    :manifest_schema_version, :manifest_json, :evidence_ref,
                    :recorded_by, :recorded_at
                )
                """
            ),
            {
                "id": entry.id,
                "activation_code": entry.activation_code,
                "adapter_code": entry.adapter_code,
                "configuration_hash": "sha256:" + "0" * 64,
                "manifest_schema_version": entry.manifest_schema_version,
                "manifest_json": entry.manifest_json,
                "evidence_ref": entry.evidence_ref,
                "recorded_by": entry.recorded_by,
                "recorded_at": entry.recorded_at,
            },
        )
    with pytest.raises(ValueError, match="manifest hash"):
        PostgresPublicFeedActivationCatalogRepository(engine).get_by_activation_code(
            entry.activation_code
        )


def test_catalog_migration_downgrade_refuses_nonempty_table_and_preserves_head() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    PostgresPublicFeedActivationCatalogRepository(engine).create_or_get(
        _entry(uuid4().hex[:10])
    )

    result = subprocess.run(
        ["alembic", "downgrade", "20260803_0025"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "cannot downgrade while public feed activation catalog entries exist" in (
        result.stdout + result.stderr
    )
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one() == "20260803_0026"

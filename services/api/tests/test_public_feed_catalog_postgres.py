from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.postgres_public_feed_catalog import (
    PostgresPublicFeedCatalogRepository,
)
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminPrincipal, AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_catalog import (
    PublicFeedCatalogService,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _definition(suffix: str, **overrides) -> PublicFeedDefinition:
    values = {
        "feed_code": f"test.pg_catalog_{suffix}.v1",
        "display_name": "PostgreSQL Catalog Feed",
        "adapter_code": f"test.pg_catalog_rss_{suffix}.v1",
        "external_locator": f"https://{suffix}.example.test/feed.xml",
        "parser_profile": StrictRssAtomParseProfile(),
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 3000,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 2,
        "terms_evidence_ref": f"evidence://terms/{suffix}",
        "rate_limit_evidence_ref": f"evidence://rate/{suffix}",
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 120,
        "permit_ttl_seconds": 30,
        "language_code": "en",
        "jurisdiction_code": "GLOBAL",
    }
    values.update(overrides)
    return PublicFeedDefinition(**values)


def _principal(at: datetime) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({AdminRole.REVIEWER}),
        direct_capabilities=frozenset(),
        authenticated_at=at - timedelta(minutes=5),
        mfa_satisfied_at=at - timedelta(minutes=5),
        step_up_at=at,
        expires_at=at + timedelta(hours=8),
        last_seen_at=at,
    )


def _service(engine, at: datetime) -> PublicFeedCatalogService:
    return PublicFeedCatalogService(
        repository=PostgresPublicFeedCatalogRepository(engine),
        security=AdminSecurityService(
            session_resolver=InMemoryAdminSessionStore(),
            policy=default_admin_security_policy(),
        ),
        clock=lambda: at,
    )


def test_postgres_registration_replay_restart_and_conflicts() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    definition = _definition(suffix)
    principal = _principal(at)
    service = _service(engine, at)

    first = service.register(principal, definition)
    replay = service.register(principal, definition)
    restarted = PostgresPublicFeedCatalogRepository(engine).get(first.id)

    assert replay == first
    assert restarted == first
    assert len(PostgresPublicFeedCatalogRepository(engine).list_audit(first.id)) == 1

    with pytest.raises(DomainError) as feed_conflict:
        service.register(
            principal,
            _definition(
                suffix,
                external_locator=f"https://changed-{suffix}.example.test/feed.xml",
            ),
        )
    assert feed_conflict.value.code == "PUBLIC_FEED_CATALOG_CONFLICT"

    with pytest.raises(DomainError) as adapter_conflict:
        service.register(
            principal,
            _definition(
                f"other-{suffix}",
                adapter_code=definition.adapter_code,
            ),
        )
    assert adapter_conflict.value.code == "PUBLIC_FEED_CATALOG_CONFLICT"


def test_postgres_lifecycle_and_ordered_audit_survive_restart() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    principal = _principal(at)
    service = _service(engine, at)
    registered = service.register(principal, _definition(suffix))
    approved = service.approve_manual_capture(principal, registered.id)
    retired = service.retire(
        principal,
        registered.id,
        rationale="Publisher retired the endpoint.",
    )

    restarted = PostgresPublicFeedCatalogRepository(engine)
    loaded = restarted.get(registered.id)
    audit = restarted.list_audit(registered.id)

    assert approved.state is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED
    assert retired.state is PublicFeedCatalogState.RETIRED
    assert loaded == retired
    assert [item.command for item in audit] == [
        "REGISTER",
        "APPROVE_MANUAL_CAPTURE",
        "RETIRE",
    ]
    assert audit[-1].rationale == "Publisher retired the endpoint."


def test_postgres_definition_lifecycle_and_audit_triggers_fail_closed() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    principal = _principal(at)
    service = _service(engine, at)
    registered = service.register(principal, _definition(suffix))

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_catalog
                    SET configuration_hash = :forged_hash
                    WHERE id = :entry_id
                    """
                ),
                {
                    "entry_id": registered.id,
                    "forged_hash": "sha256:" + "0" * 64,
                },
            )

    approved = service.approve_manual_capture(principal, registered.id)
    assert approved.state is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_catalog
                    SET lifecycle_state = 'REGISTERED',
                        approved_by = NULL,
                        approved_at = NULL
                    WHERE id = :entry_id
                    """
                ),
                {"entry_id": registered.id},
            )

    audit_id = PostgresPublicFeedCatalogRepository(engine).list_audit(
        registered.id
    )[0].audit_id
    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_catalog_audit
                    SET command = 'FORGED'
                    WHERE audit_id = :audit_id
                    """
                ),
                {"audit_id": audit_id},
            )
    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.public_feed_catalog_audit
                    WHERE audit_id = :audit_id
                    """
                ),
                {"audit_id": audit_id},
            )

    loaded = PostgresPublicFeedCatalogRepository(engine).get(registered.id)
    assert loaded == approved
    assert [
        item.command
        for item in PostgresPublicFeedCatalogRepository(engine).list_audit(
            registered.id
        )
    ] == ["REGISTER", "APPROVE_MANUAL_CAPTURE"]

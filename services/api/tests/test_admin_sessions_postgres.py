from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.postgres_admin_security import PostgresAdminSessionStore
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminRole,
    AdminSessionStatus,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

# Keep scenario-relative assertions deterministic within the module while ensuring
# sessions created for integration tests are actually live at wall-clock resolution
# time. A fixed calendar date eventually turns this fixture into an accidental expiry
# test and masks the behavior each test is intended to exercise.
NOW = datetime.now(UTC).replace(microsecond=0)


def _engine():
    return create_engine(os.environ["KEFE_DATABASE_URL"])


def _subject_with_access(
    *,
    roles: tuple[AdminRole, ...],
    capability: AdminCapability | None = None,
):
    engine = _engine()
    subject_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO admin_security.subject (id, state)
                VALUES (:id, 'ACTIVE')
                """
            ),
            {"id": subject_id},
        )
        for role in roles:
            connection.execute(
                text(
                    """
                    INSERT INTO admin_security.role_assignment (
                        id, subject_id, role, granted_at
                    ) VALUES (:id, :subject_id, :role, :granted_at)
                    """
                ),
                {
                    "id": uuid4(),
                    "subject_id": subject_id,
                    "role": role.value,
                    "granted_at": NOW,
                },
            )
        if capability is not None:
            connection.execute(
                text(
                    """
                    INSERT INTO admin_security.capability_grant (
                        id, subject_id, capability, granted_at
                    ) VALUES (:id, :subject_id, :capability, :granted_at)
                    """
                ),
                {
                    "id": uuid4(),
                    "subject_id": subject_id,
                    "capability": capability.value,
                    "granted_at": NOW,
                },
            )
    return engine, subject_id


def test_postgres_admin_session_stores_only_hashes_and_resolves_access() -> None:
    engine, subject_id = _subject_with_access(
        roles=(AdminRole.EDITOR,),
        capability=AdminCapability.AUDIT_READ,
    )
    store = PostgresAdminSessionStore(engine)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=12),
    )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT token_hash, csrf_token_hash, last_seen_at
                FROM admin_security.session
                WHERE id = :session_id
                """
            ),
            {"session_id": issued.session_id},
        ).mappings().one()

    assert row["token_hash"] == hashlib.sha256(issued.session_token.encode()).hexdigest()
    assert row["csrf_token_hash"] == hashlib.sha256(issued.csrf_token.encode()).hexdigest()
    assert issued.session_token not in {row["token_hash"], row["csrf_token_hash"]}
    assert issued.csrf_token not in {row["token_hash"], row["csrf_token_hash"]}

    resolution = store.resolve(issued.session_token)
    assert resolution.status is AdminSessionStatus.ACTIVE
    assert resolution.principal is not None
    assert resolution.principal.admin_subject_id == subject_id
    assert resolution.principal.roles == frozenset({AdminRole.EDITOR})
    assert resolution.principal.direct_capabilities == frozenset({AdminCapability.AUDIT_READ})


def test_admin_authentication_marks_seen_only_after_idle_check() -> None:
    engine, subject_id = _subject_with_access(roles=(AdminRole.EDITOR,))
    store = PostgresAdminSessionStore(engine)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW - timedelta(minutes=10),
        mfa_satisfied_at=NOW - timedelta(minutes=10),
        expires_at=NOW + timedelta(hours=11),
    )
    security = AdminSecurityService(
        session_resolver=store,
        policy=default_admin_security_policy(),
    )

    principal = security.authenticate(issued.session_token, now=NOW)
    assert principal.admin_subject_id == subject_id
    refreshed = store.resolve(issued.session_token)
    assert refreshed.principal is not None
    assert refreshed.principal.last_seen_at == NOW

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE admin_security.session
                SET last_seen_at = :last_seen_at
                WHERE id = :session_id
                """
            ),
            {
                "session_id": issued.session_id,
                "last_seen_at": NOW - timedelta(minutes=31),
            },
        )

    with pytest.raises(DomainError) as expired:
        security.authenticate(issued.session_token, now=NOW)
    assert expired.value.code == "ADMIN_SESSION_EXPIRED"

    with engine.connect() as connection:
        last_seen = connection.execute(
            text(
                """
                SELECT last_seen_at
                FROM admin_security.session
                WHERE id = :session_id
                """
            ),
            {"session_id": issued.session_id},
        ).scalar_one()
    assert last_seen == NOW - timedelta(minutes=31)


def test_csrf_is_bound_to_same_session_and_revocation_is_immediate() -> None:
    engine, subject_id = _subject_with_access(roles=(AdminRole.PUBLISHER,))
    store = PostgresAdminSessionStore(engine)
    first = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=12),
    )
    second = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=12),
    )

    assert store.verify(session_token=first.session_token, csrf_token=first.csrf_token)
    assert store.verify(session_token=second.session_token, csrf_token=second.csrf_token)
    assert not store.verify(session_token=first.session_token, csrf_token=second.csrf_token)
    assert not store.verify(session_token=second.session_token, csrf_token=first.csrf_token)

    store.record_step_up(first.session_id, step_up_at=NOW + timedelta(minutes=1))
    stepped = store.resolve(first.session_token)
    assert stepped.principal is not None
    assert stepped.principal.step_up_at == NOW + timedelta(minutes=1)

    store.revoke(first.session_id, revoked_at=NOW + timedelta(minutes=2))
    assert store.resolve(first.session_token).status is AdminSessionStatus.REVOKED
    assert not store.verify(session_token=first.session_token, csrf_token=first.csrf_token)
    assert store.resolve(second.session_token).status is AdminSessionStatus.ACTIVE


def test_suspended_subject_invalidates_existing_admin_session() -> None:
    engine, subject_id = _subject_with_access(roles=(AdminRole.REVIEWER,))
    store = PostgresAdminSessionStore(engine)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=12),
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE admin_security.subject
                SET state = 'SUSPENDED', updated_at = now()
                WHERE id = :subject_id
                """
            ),
            {"subject_id": subject_id},
        )

    assert store.resolve(issued.session_token).status is AdminSessionStatus.REVOKED
    assert not store.verify(session_token=issued.session_token, csrf_token=issued.csrf_token)


def test_expired_admin_session_is_not_resolved_as_active() -> None:
    engine, subject_id = _subject_with_access(roles=(AdminRole.EDITOR,))
    store = PostgresAdminSessionStore(engine)
    wall_now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=wall_now - timedelta(hours=2),
        mfa_satisfied_at=wall_now - timedelta(hours=2),
        expires_at=wall_now - timedelta(hours=1),
    )

    assert store.resolve(issued.session_token).status is AdminSessionStatus.EXPIRED

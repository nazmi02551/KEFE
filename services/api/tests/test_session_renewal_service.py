from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.models import ActorKind
from kefe_api.modules.identity.session_renewal import (
    SessionContinuityPolicy,
    SessionTokenDeriver,
)
from kefe_api.modules.identity.session_renewal_service import SessionRenewalService


_ACTOR_ID = UUID("12345678-1234-4234-8234-1234567890ab")
_SESSION_ID = UUID("abcdefab-cdef-4def-8def-abcdefabcdef")
_SECRET = "session-renewal-service-test-secret-0001"


def _runtime() -> tuple[
    InMemoryIdentityRepository,
    SessionRenewalService,
    SessionTokenDeriver,
    str,
]:
    now = datetime.now(UTC)
    policy = SessionContinuityPolicy.from_days(
        access_ttl_days=30,
        absolute_lifetime_days=180,
        inactivity_lifetime_days=60,
        previous_pair_grace_seconds=60,
    )
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
    )
    pair = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=0,
    )
    absolute, inactive = policy.initial_deadlines(now=now)
    repository = InMemoryIdentityRepository()
    repository.create_guest_session(
        actor_id=_ACTOR_ID,
        session_id=_SESSION_ID,
        token_hash=deriver.token_hash(pair.access_token),
        expires_at=now + policy.access_ttl,
        renewal_token_hash=deriver.token_hash(pair.renewal_token),
        rotation_counter=0,
        token_derivation_key_id=pair.derivation_key_id,
        continuity_absolute_expires_at=absolute,
        continuity_inactive_expires_at=inactive,
    )
    service = SessionRenewalService(
        repository=repository,
        policy=policy,
        deriver=deriver,
    )
    return repository, service, deriver, pair.renewal_token


def test_renew_rotates_same_actor_without_new_identity() -> None:
    _, service, _, renewal_token = _runtime()

    credential = service.renew(renewal_token=renewal_token)

    assert credential.actor_id == _ACTOR_ID
    assert credential.actor_kind is ActorKind.GUEST
    assert credential.rotation_counter == 1
    assert credential.renewal_token != renewal_token


def test_previous_renewal_retry_returns_already_current_pair() -> None:
    _, service, _, renewal_token = _runtime()

    first = service.renew(renewal_token=renewal_token)
    retry = service.renew(renewal_token=renewal_token)

    assert retry == first


def test_current_rotated_renewal_can_rotate_again() -> None:
    _, service, _, renewal_token = _runtime()

    first = service.renew(renewal_token=renewal_token)
    second = service.renew(renewal_token=first.renewal_token)

    assert second.actor_id == first.actor_id
    assert second.rotation_counter == 2
    assert second.renewal_token != first.renewal_token


def test_revoked_session_cannot_renew() -> None:
    repository, service, deriver, renewal_token = _runtime()
    access = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=0,
    ).access_token
    repository.revoke_token(
        token_hash=deriver.token_hash(access),
        now=datetime.now(UTC),
    )

    with pytest.raises(DomainError) as exc_info:
        service.renew(renewal_token=renewal_token)

    assert exc_info.value.code == "AUTH_TOKEN_REVOKED"


def test_continuity_deadline_blocks_renewal() -> None:
    now = datetime.now(UTC)
    policy = SessionContinuityPolicy.from_days(
        access_ttl_days=30,
        absolute_lifetime_days=180,
        inactivity_lifetime_days=60,
        previous_pair_grace_seconds=60,
    )
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
    )
    pair = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=0,
    )
    repository = InMemoryIdentityRepository()
    repository.create_guest_session(
        actor_id=_ACTOR_ID,
        session_id=_SESSION_ID,
        token_hash=deriver.token_hash(pair.access_token),
        expires_at=now - timedelta(seconds=1),
        renewal_token_hash=deriver.token_hash(pair.renewal_token),
        rotation_counter=0,
        token_derivation_key_id=pair.derivation_key_id,
        continuity_absolute_expires_at=now + timedelta(days=120),
        continuity_inactive_expires_at=now - timedelta(seconds=1),
    )
    service = SessionRenewalService(
        repository=repository,
        policy=policy,
        deriver=deriver,
    )

    with pytest.raises(DomainError) as exc_info:
        service.renew(renewal_token=pair.renewal_token)

    assert exc_info.value.code == "AUTH_SESSION_CONTINUITY_EXPIRED"

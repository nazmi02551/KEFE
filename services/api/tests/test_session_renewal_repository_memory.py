from datetime import UTC, datetime, timedelta
from uuid import UUID

from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.session_renewal import (
    RenewalResolutionStatus,
    RenewalTokenMatch,
    SessionRotationMutation,
)

_ACTOR_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_SESSION_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def _repository(now: datetime) -> InMemoryIdentityRepository:
    repository = InMemoryIdentityRepository()
    repository.create_guest_session(
        actor_id=_ACTOR_ID,
        session_id=_SESSION_ID,
        token_hash="a" * 64,
        expires_at=now + timedelta(days=30),
        renewal_token_hash="b" * 64,
        rotation_counter=0,
        token_derivation_key_id="primary-v1",
        continuity_absolute_expires_at=now + timedelta(days=180),
        continuity_inactive_expires_at=now + timedelta(days=60),
    )
    return repository


def test_current_renewal_resolves_active_snapshot() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    repository = _repository(now)

    resolution = repository.resolve_renewal(
        renewal_token_hash="b" * 64,
        now=now,
    )

    assert resolution.status is RenewalResolutionStatus.ACTIVE
    assert resolution.snapshot is not None
    assert resolution.snapshot.session_id == _SESSION_ID
    assert resolution.snapshot.rotation_counter == 0
    assert resolution.snapshot.token_match is RenewalTokenMatch.CURRENT


def test_rotation_is_compare_and_swap_and_preserves_previous_pair_grace() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    repository = _repository(now)
    mutation = SessionRotationMutation(
        session_id=_SESSION_ID,
        expected_rotation_counter=0,
        current_access_token_hash="a" * 64,
        current_renewal_token_hash="b" * 64,
        next_access_token_hash="c" * 64,
        next_renewal_token_hash="d" * 64,
        next_access_expires_at=now + timedelta(days=30),
        next_inactive_expires_at=now + timedelta(days=60),
        next_rotation_counter=1,
        next_derivation_key_id="primary-v1",
        previous_pair_valid_until=now + timedelta(seconds=60),
        renewed_at=now,
    )

    assert repository.rotate_session(mutation=mutation) is True
    assert repository.rotate_session(mutation=mutation) is False

    previous = repository.resolve_renewal(
        renewal_token_hash="b" * 64,
        now=now + timedelta(seconds=30),
    )
    current = repository.resolve_renewal(
        renewal_token_hash="d" * 64,
        now=now + timedelta(seconds=30),
    )

    assert previous.status is RenewalResolutionStatus.ACTIVE
    assert previous.snapshot is not None
    assert previous.snapshot.token_match is RenewalTokenMatch.PREVIOUS_GRACE
    assert previous.snapshot.rotation_counter == 1
    assert current.status is RenewalResolutionStatus.ACTIVE
    assert current.snapshot is not None
    assert current.snapshot.token_match is RenewalTokenMatch.CURRENT
    assert current.snapshot.rotation_counter == 1


def test_previous_renewal_is_invalid_after_grace() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    repository = _repository(now)
    mutation = SessionRotationMutation(
        session_id=_SESSION_ID,
        expected_rotation_counter=0,
        current_access_token_hash="a" * 64,
        current_renewal_token_hash="b" * 64,
        next_access_token_hash="c" * 64,
        next_renewal_token_hash="d" * 64,
        next_access_expires_at=now + timedelta(days=30),
        next_inactive_expires_at=now + timedelta(days=60),
        next_rotation_counter=1,
        next_derivation_key_id="primary-v1",
        previous_pair_valid_until=now + timedelta(seconds=60),
        renewed_at=now,
    )
    assert repository.rotate_session(mutation=mutation) is True

    resolution = repository.resolve_renewal(
        renewal_token_hash="b" * 64,
        now=now + timedelta(seconds=61),
    )

    assert resolution.status is RenewalResolutionStatus.INVALID


def test_continuity_expiry_fails_closed() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    repository = _repository(now)

    resolution = repository.resolve_renewal(
        renewal_token_hash="b" * 64,
        now=now + timedelta(days=60),
    )

    assert resolution.status is RenewalResolutionStatus.CONTINUITY_EXPIRED


def test_revocation_blocks_renewal() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    repository = _repository(now)
    repository.revoke_token(token_hash="a" * 64, now=now)

    resolution = repository.resolve_renewal(
        renewal_token_hash="b" * 64,
        now=now,
    )

    assert resolution.status is RenewalResolutionStatus.REVOKED

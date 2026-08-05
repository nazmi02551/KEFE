from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.identity.account_in_memory import InMemoryAccountContinuityRepository
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.models import ActorKind, TokenStatus


def test_account_conversion_rotates_guest_sessions_and_preserves_account_sessions() -> None:
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=30)
    identity = InMemoryIdentityRepository()
    accounts = InMemoryAccountContinuityRepository(identity)

    first_guest_id = uuid4()
    identity.create_guest_session(
        actor_id=first_guest_id,
        token_hash="first-guest-token",
        expires_at=expires_at,
    )
    promoted_actor_id, merged_from = accounts.upgrade_or_merge_guest(
        guest_actor_id=first_guest_id,
        identifier_hash="verified-account",
        channel=OtpChannel.EMAIL,
        identifier_hint="fi***@example.test",
        verified_at=now,
    )
    assert promoted_actor_id == first_guest_id
    assert merged_from is None
    assert identity.resolve_token(token_hash="first-guest-token", now=now).status is (
        TokenStatus.REVOKED
    )

    accounts.create_account_session(
        actor_id=promoted_actor_id,
        token_hash="account-token",
        expires_at=expires_at,
    )
    account_resolution = identity.resolve_token(token_hash="account-token", now=now)
    assert account_resolution.status is TokenStatus.ACTIVE
    assert account_resolution.principal is not None
    assert account_resolution.principal.actor_kind is ActorKind.ACCOUNT

    second_guest_id = uuid4()
    identity.create_guest_session(
        actor_id=second_guest_id,
        token_hash="second-guest-token",
        expires_at=expires_at,
    )
    merged_actor_id, merged_from = accounts.upgrade_or_merge_guest(
        guest_actor_id=second_guest_id,
        identifier_hash="verified-account",
        channel=OtpChannel.EMAIL,
        identifier_hint="fi***@example.test",
        verified_at=now + timedelta(seconds=1),
    )

    assert merged_actor_id == promoted_actor_id
    assert merged_from == second_guest_id
    assert identity.resolve_token(token_hash="second-guest-token", now=now).status is (
        TokenStatus.REVOKED
    )
    assert identity.resolve_token(token_hash="account-token", now=now).status is (
        TokenStatus.ACTIVE
    )

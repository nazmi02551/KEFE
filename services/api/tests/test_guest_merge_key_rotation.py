from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET
from kefe_api.modules.identity.account_in_memory import (
    InMemoryAccountContinuityRepository,
)
from kefe_api.modules.identity.account_models import OtpChannel, OtpVerification
from kefe_api.modules.identity.account_service import AccountContinuityService
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.models import (
    ActorKind,
    ActorPrincipal,
    TokenResolution,
    TokenStatus,
)
from kefe_api.modules.identity.otp_delivery import CapturingOtpDelivery

OLD_SECRET = "old-guest-merge-replay-secret-0123456789012345"
NEW_SECRET = "new-guest-merge-replay-secret-0123456789012345"
FUTURE_SECRET = "future-guest-merge-replay-secret-012345678901"


def _service(
    repository: InMemoryAccountContinuityRepository,
    delivery: CapturingOtpDelivery,
    *,
    active_key_id: str,
    active_secret: str,
    retained_keys: dict[str, str] | None = None,
    environment: str = "development",
) -> AccountContinuityService:
    return AccountContinuityService(
        repository=repository,
        delivery=delivery,
        environment=environment,
        account_merge_replay_active_key_id=active_key_id,
        account_merge_replay_secret=active_secret,
        account_merge_replay_retained_keys=retained_keys or {},
    )


def _verification_token(
    service: AccountContinuityService,
    delivery: CapturingOtpDelivery,
    email: str,
) -> str:
    challenge = service.request_otp(channel=OtpChannel.EMAIL, identifier=email)
    code = delivery.code_for(channel=OtpChannel.EMAIL, identifier=email)
    assert code is not None
    token, _ = service.verify_otp(challenge_id=challenge.id, code=code)
    return token


def _authorization(actor_id: UUID, status: TokenStatus) -> TokenResolution:
    return TokenResolution(
        status,
        ActorPrincipal(actor_id=actor_id, actor_kind=ActorKind.GUEST),
    )


def _store_legacy_verification(
    repository: InMemoryAccountContinuityRepository,
    delivery: CapturingOtpDelivery,
    service: AccountContinuityService,
    token: str,
) -> None:
    challenge = service.request_otp(
        channel=OtpChannel.EMAIL,
        identifier="legacy@example.test",
    )
    now = datetime.now(UTC)
    verification = OtpVerification(
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        identifier_hash=challenge.identifier_hash,
        channel=challenge.channel,
        identifier_hint=challenge.identifier_hint,
        verified_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    assert repository.consume_challenge(
        challenge_id=challenge.id,
        consumed_at=now,
        verification=verification,
    )
    assert delivery.code_for(
        channel=OtpChannel.EMAIL,
        identifier="legacy@example.test",
    ) is not None


def test_legacy_v1_replay_derivation_remains_byte_compatible() -> None:
    identity = InMemoryIdentityRepository()
    repository = InMemoryAccountContinuityRepository(identity)
    delivery = CapturingOtpDelivery()
    service = _service(
        repository,
        delivery,
        active_key_id="primary-v1",
        active_secret=OLD_SECRET,
    )
    actor_id = uuid4()
    verification_token = f"kefe_v_{secrets.token_urlsafe(32)}"
    _store_legacy_verification(repository, delivery, service, verification_token)

    credential = service.merge_guest(
        authorization=_authorization(actor_id, TokenStatus.ACTIVE),
        verification_token=verification_token,
    )

    token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
    expiry = credential.expires_at.astimezone(UTC).isoformat(timespec="microseconds")
    message = (
        f"kefe:guest-account-merge:v1:{token_hash}:{actor_id}:{expiry}"
    ).encode()
    digest = hmac.new(OLD_SECRET.encode(), message, hashlib.sha256).digest()
    expected = f"kefe_a_{base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')}"
    assert credential.access_token == expected


def test_active_key_rotation_preserves_exact_replay_through_retained_key() -> None:
    identity = InMemoryIdentityRepository()
    repository = InMemoryAccountContinuityRepository(identity)
    delivery = CapturingOtpDelivery()
    old_service = _service(
        repository,
        delivery,
        active_key_id="old-2026",
        active_secret=OLD_SECRET,
    )
    actor_id = uuid4()
    verification_token = _verification_token(
        old_service,
        delivery,
        "rotation@example.test",
    )
    assert verification_token.startswith("kefe_v2.old-2026.")
    first = old_service.merge_guest(
        authorization=_authorization(actor_id, TokenStatus.ACTIVE),
        verification_token=verification_token,
    )

    rotated_service = _service(
        repository,
        delivery,
        active_key_id="new-2026",
        active_secret=NEW_SECRET,
        retained_keys={"old-2026": OLD_SECRET},
    )
    replay = rotated_service.merge_guest(
        authorization=_authorization(actor_id, TokenStatus.REVOKED),
        verification_token=verification_token,
    )
    assert replay == first

    new_actor_id = uuid4()
    new_verification = _verification_token(
        rotated_service,
        delivery,
        "new-active@example.test",
    )
    assert new_verification.startswith("kefe_v2.new-2026.")
    new_credential = rotated_service.merge_guest(
        authorization=_authorization(new_actor_id, TokenStatus.ACTIVE),
        verification_token=new_verification,
    )
    assert new_credential.access_token != first.access_token


def test_missing_retained_key_for_live_replay_fails_closed() -> None:
    identity = InMemoryIdentityRepository()
    repository = InMemoryAccountContinuityRepository(identity)
    delivery = CapturingOtpDelivery()
    old_service = _service(
        repository,
        delivery,
        active_key_id="old-2026",
        active_secret=OLD_SECRET,
    )
    actor_id = uuid4()
    verification_token = _verification_token(
        old_service,
        delivery,
        "missing@example.test",
    )
    old_service.merge_guest(
        authorization=_authorization(actor_id, TokenStatus.ACTIVE),
        verification_token=verification_token,
    )

    unsafe_service = _service(
        repository,
        delivery,
        active_key_id="new-2026",
        active_secret=NEW_SECRET,
    )
    with pytest.raises(DomainError) as captured:
        unsafe_service.merge_guest(
            authorization=_authorization(actor_id, TokenStatus.REVOKED),
            verification_token=verification_token,
        )
    assert captured.value.code == "DEPENDENCY_TEMPORARILY_UNAVAILABLE"
    assert captured.value.retryable is True


def test_expired_replay_does_not_require_retired_key() -> None:
    identity = InMemoryIdentityRepository()
    repository = InMemoryAccountContinuityRepository(identity)
    delivery = CapturingOtpDelivery()
    old_service = _service(
        repository,
        delivery,
        active_key_id="old-2026",
        active_secret=OLD_SECRET,
    )
    actor_id = uuid4()
    verification_token = _verification_token(
        old_service,
        delivery,
        "expired@example.test",
    )
    token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
    completed_at = datetime.now(UTC)
    repository.complete_guest_merge(
        source_actor_id=actor_id,
        verification_token_hash=token_hash,
        account_token_hash="0" * 64,
        account_session_expires_at=completed_at - timedelta(seconds=1),
        completed_at=completed_at,
    )

    retired_service = _service(
        repository,
        delivery,
        active_key_id="new-2026",
        active_secret=NEW_SECRET,
    )
    with pytest.raises(DomainError) as captured:
        retired_service.merge_guest(
            authorization=_authorization(actor_id, TokenStatus.REVOKED),
            verification_token=verification_token,
        )
    assert captured.value.code == "AUTH_TOKEN_EXPIRED"


@pytest.mark.parametrize(
    ("active_key_id", "active_secret", "retained_keys", "match"),
    [
        ("bad.key", OLD_SECRET, {}, "active key id"),
        ("active", OLD_SECRET, {"active": NEW_SECRET}, "duplicated"),
        ("active", OLD_SECRET, {"old": OLD_SECRET}, "must be unique"),
        ("active", "short", {}, "at least 32"),
    ],
)
def test_invalid_keyring_configuration_is_rejected(
    active_key_id: str,
    active_secret: str,
    retained_keys: dict[str, str],
    match: str,
) -> None:
    repository = InMemoryAccountContinuityRepository(InMemoryIdentityRepository())
    with pytest.raises(ValueError, match=match):
        _service(
            repository,
            CapturingOtpDelivery(),
            active_key_id=active_key_id,
            active_secret=active_secret,
            retained_keys=retained_keys,
        )


def test_production_rejects_development_secret_anywhere_in_keyring() -> None:
    repository = InMemoryAccountContinuityRepository(InMemoryIdentityRepository())
    with pytest.raises(ValueError, match="secret management"):
        _service(
            repository,
            CapturingOtpDelivery(),
            active_key_id="active",
            active_secret=NEW_SECRET,
            retained_keys={"legacy": DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET},
            environment="production",
        )


def test_production_accepts_managed_active_and_retained_keys() -> None:
    repository = InMemoryAccountContinuityRepository(InMemoryIdentityRepository())
    service = _service(
        repository,
        CapturingOtpDelivery(),
        active_key_id="active-2026",
        active_secret=NEW_SECRET,
        retained_keys={"future-2026": FUTURE_SECRET, "old-2026": OLD_SECRET},
        environment="production",
    )
    assert service is not None

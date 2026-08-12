from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from kefe_api.modules.identity.models import ActorKind
from kefe_api.modules.identity.session_renewal import (
    SessionContinuityPolicy,
    SessionTokenDeriver,
)


_SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
_ACTOR_ID = UUID("22222222-2222-4222-8222-222222222222")
_SECRET = "session-renewal-test-secret-material-0001"
_RETAINED_SECRET = "session-renewal-test-secret-material-0000"


def _policy() -> SessionContinuityPolicy:
    return SessionContinuityPolicy.from_days(
        access_ttl_days=30,
        absolute_lifetime_days=180,
        inactivity_lifetime_days=60,
        previous_pair_grace_seconds=60,
    )


def test_continuity_policy_anchors_absolute_and_inactivity_deadlines() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)

    absolute, inactive = _policy().initial_deadlines(now=now)

    assert absolute == now + timedelta(days=180)
    assert inactive == now + timedelta(days=60)


def test_successful_renewal_never_extends_absolute_deadline() -> None:
    policy = _policy()
    created_at = datetime(2026, 8, 12, tzinfo=UTC)
    absolute, _ = policy.initial_deadlines(now=created_at)
    near_absolute = absolute - timedelta(days=10)

    renewed_inactive = policy.renewed_inactivity_deadline(
        now=near_absolute,
        absolute_expires_at=absolute,
    )

    assert renewed_inactive == absolute


def test_policy_rejects_inactivity_not_longer_than_access_ttl() -> None:
    with pytest.raises(ValueError, match="inactivity lifetime must exceed access TTL"):
        SessionContinuityPolicy.from_days(
            access_ttl_days=30,
            absolute_lifetime_days=180,
            inactivity_lifetime_days=30,
            previous_pair_grace_seconds=60,
        )


def test_token_derivation_is_deterministic_and_domain_separated() -> None:
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
    )

    first = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=3,
    )
    repeated = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=3,
    )

    assert first == repeated
    assert first.access_token.startswith("kefe_g_")
    assert first.renewal_token.startswith("kefe_r_")
    assert first.access_token.removeprefix("kefe_g_") != first.renewal_token.removeprefix(
        "kefe_r_"
    )


def test_rotation_counter_changes_both_credentials() -> None:
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
    )

    current = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.ACCOUNT,
        rotation_counter=0,
    )
    rotated = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.ACCOUNT,
        rotation_counter=1,
    )

    assert current.access_token != rotated.access_token
    assert current.renewal_token != rotated.renewal_token
    assert rotated.access_token.startswith("kefe_a_")


def test_retained_key_can_reproduce_previous_pair() -> None:
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
        retained_keys={"previous-v1": _RETAINED_SECRET},
    )

    previous = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=7,
        key_id="previous-v1",
    )
    repeated = deriver.derive_pair(
        session_id=_SESSION_ID,
        actor_id=_ACTOR_ID,
        actor_kind=ActorKind.GUEST,
        rotation_counter=7,
        key_id="previous-v1",
    )

    assert previous == repeated
    assert previous.derivation_key_id == "previous-v1"


def test_unknown_derivation_key_fails_closed() -> None:
    deriver = SessionTokenDeriver(
        active_key_id="primary-v1",
        active_secret=_SECRET,
    )

    with pytest.raises(ValueError, match="unknown session token derivation key id"):
        deriver.derive_pair(
            session_id=_SESSION_ID,
            actor_id=_ACTOR_ID,
            actor_kind=ActorKind.GUEST,
            rotation_counter=0,
            key_id="missing-v1",
        )

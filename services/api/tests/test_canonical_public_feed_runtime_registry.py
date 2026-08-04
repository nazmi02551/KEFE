from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytest

from kefe_api.infrastructure.canonical_public_feed_runtime import (
    CanonicalPublicFeedRuntimeProfileRegistry,
    MutableProviderAdoptionRegistry,
    MutablePublicSourceCaptureRegistry,
)
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    PublicFeedRuntimeProfile,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomCaptureDefinition,
    StrictRssAtomParseProfile,
)


@dataclass(frozen=True)
class _Adapter:
    adapter_code: str

    def capture(self, *, external_locator: str, trace_id: str, at: datetime):
        raise AssertionError((external_locator, trace_id, at))


class _Factory:
    def create(self, definition: StrictRssAtomCaptureDefinition) -> _Adapter:
        return _Adapter(definition.adapter_code)


def _profile(*, adapter_code: str = "kefe.public_feed.registry.v1") -> PublicFeedRuntimeProfile:
    definition = PublicFeedDefinition(
        feed_code="registry-feed",
        display_name="Registry Feed",
        adapter_code=adapter_code,
        external_locator="https://feeds.example.test/registry.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1000,
        read_timeout_ms=2000,
        total_timeout_ms=3000,
        max_response_bytes=2_000_000,
        max_redirect_hops=1,
        terms_evidence_ref="evidence://provider-terms/registry/v1",
        rate_limit_evidence_ref="evidence://provider-rate/registry/v1",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )
    return PublicFeedRuntimeProfile(
        feed_definition_id=uuid4(),
        configuration_hash=f"sha256:{'1' * 64}",
        adoption_profile=definition.to_adoption_profile(),
        capture_definition=StrictRssAtomCaptureDefinition(
            adapter_code=definition.adapter_code,
            profile=definition.parser_profile,
        ),
        acquisition_command=definition.acquisition_command(),
    )


def test_runtime_registry_is_empty_until_explicit_registration() -> None:
    adoption = MutableProviderAdoptionRegistry()
    capture = MutablePublicSourceCaptureRegistry()
    registry = CanonicalPublicFeedRuntimeProfileRegistry(
        adoption=adoption,
        capture=capture,
        adapter_factory=_Factory(),  # type: ignore[arg-type]
    )
    profile = _profile()

    assert registry.adapter_codes() == ()
    assert adoption.adapter_codes() == ()
    assert capture.adapter_codes() == ()

    stored = registry.register_or_get(profile)
    assert stored == profile
    assert registry.register_or_get(profile) == profile
    assert registry.get(profile.adoption_profile.adapter_code) == profile
    assert adoption.get(profile.adoption_profile.adapter_code) == profile.adoption_profile
    assert capture.get(profile.adoption_profile.adapter_code).adapter_code == (
        profile.adoption_profile.adapter_code
    )


def test_runtime_registry_rejects_same_adapter_with_different_profile() -> None:
    adoption = MutableProviderAdoptionRegistry()
    capture = MutablePublicSourceCaptureRegistry()
    registry = CanonicalPublicFeedRuntimeProfileRegistry(
        adoption=adoption,
        capture=capture,
        adapter_factory=_Factory(),  # type: ignore[arg-type]
    )
    first = _profile()
    registry.register_or_get(first)
    conflicting = PublicFeedRuntimeProfile(
        feed_definition_id=uuid4(),
        configuration_hash=f"sha256:{'2' * 64}",
        adoption_profile=first.adoption_profile,
        capture_definition=first.capture_definition,
        acquisition_command=first.acquisition_command,
    )

    with pytest.raises(ValueError, match="conflicts"):
        registry.register_or_get(conflicting)


def test_runtime_registry_requires_one_adapter_identity() -> None:
    profile = _profile()
    invalid = PublicFeedRuntimeProfile(
        feed_definition_id=profile.feed_definition_id,
        configuration_hash=profile.configuration_hash,
        adoption_profile=profile.adoption_profile,
        capture_definition=StrictRssAtomCaptureDefinition(
            adapter_code="kefe.public_feed.other.v1",
            profile=StrictRssAtomParseProfile(),
        ),
        acquisition_command=profile.acquisition_command,
    )
    registry = CanonicalPublicFeedRuntimeProfileRegistry(
        adoption=MutableProviderAdoptionRegistry(),
        capture=MutablePublicSourceCaptureRegistry(),
        adapter_factory=_Factory(),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="adapter identity mismatch"):
        registry.register_or_get(invalid)

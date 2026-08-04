from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedCatalogService,
    CanonicalPublicFeedDefinition,
    InMemoryPublicFeedCatalogRepository,
    InMemoryPublicFeedRuntimeProfileRegistry,
    PublicFeedActivationProjection,
    PublicFeedActivationState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

NOW = datetime(2026, 8, 4, 14, 0, tzinfo=UTC)


class _UnusedDependency:
    def __getattr__(self, name: str):
        raise AssertionError(f"rehydration must not call dependency method {name}")


def _approved_definition(
    feed_code: str,
    *,
    version: int = 1,
) -> CanonicalPublicFeedDefinition:
    public = PublicFeedDefinition(
        feed_code=feed_code,
        display_name=f"{feed_code} feed",
        adapter_code=f"kefe.public_feed.{feed_code}.v{version}",
        external_locator=f"https://feeds.example.test/{feed_code}.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1000,
        read_timeout_ms=2000,
        total_timeout_ms=3000,
        max_response_bytes=2_000_000,
        max_redirect_hops=1,
        terms_evidence_ref=f"evidence://provider-terms/{feed_code}/v1",
        rate_limit_evidence_ref=f"evidence://provider-rate/{feed_code}/v1",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )
    draft = CanonicalPublicFeedDefinition.create(
        definition_version=version,
        definition=public,
        interval_seconds=300,
        max_dispatch_attempts=3,
        created_at=NOW,
        created_by_actor_ref="admin:creator",
    )
    preflighted = draft.mark_preflight(
        actor_ref="admin:creator",
        at=NOW + timedelta(seconds=1),
    )
    return preflighted.approve(
        actor_ref="admin:approver",
        at=NOW + timedelta(seconds=2),
    )


def _service(
    repository: InMemoryPublicFeedCatalogRepository,
    runtime: InMemoryPublicFeedRuntimeProfileRegistry,
) -> CanonicalPublicFeedCatalogService:
    unused = _UnusedDependency()
    return CanonicalPublicFeedCatalogService(
        repository=repository,
        security=unused,  # type: ignore[arg-type]
        provider_admission=unused,  # type: ignore[arg-type]
        runtime_profiles=runtime,
        scheduler=unused,  # type: ignore[arg-type]
        clock=lambda: NOW,
    )


def test_rehydration_registers_active_and_paused_profiles_without_side_effects() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    active_definition = _approved_definition("rehydrate-active")
    paused_definition = _approved_definition("rehydrate-paused")
    retired_definition = _approved_definition("rehydrate-retired")
    for definition in (
        active_definition,
        paused_definition,
        retired_definition,
    ):
        repository.add_definition(definition)

    active = PublicFeedActivationProjection.create(
        definition=active_definition,
        schedule_id=uuid4(),
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=3),
    )
    paused = PublicFeedActivationProjection.create(
        definition=paused_definition,
        schedule_id=uuid4(),
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=3),
    ).transition(
        PublicFeedActivationState.PAUSED,
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=4),
    )
    retired = PublicFeedActivationProjection.create(
        definition=retired_definition,
        schedule_id=uuid4(),
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=3),
    ).transition(
        PublicFeedActivationState.RETIRED,
        actor_ref="admin:activator",
        at=NOW + timedelta(seconds=4),
    )
    repository.add_activation(active)
    repository.add_activation(paused)
    repository.add_activation(retired)

    runtime = InMemoryPublicFeedRuntimeProfileRegistry()
    service = _service(repository, runtime)

    assert service.rehydrate_runtime_profiles() == tuple(
        sorted((active.adapter_code, paused.adapter_code))
    )
    assert runtime.get(active.adapter_code) is not None
    assert runtime.get(paused.adapter_code) is not None
    assert runtime.get(retired.adapter_code) is None
    assert service.rehydrate_runtime_profiles() == tuple(
        sorted((active.adapter_code, paused.adapter_code))
    )


def test_rehydration_fails_closed_on_persisted_hash_or_adapter_drift() -> None:
    definition = _approved_definition("rehydrate-drift")

    for activation in (
        replace(
            PublicFeedActivationProjection.create(
                definition=definition,
                schedule_id=uuid4(),
                actor_ref="admin:activator",
                at=NOW + timedelta(seconds=3),
            ),
            configuration_hash=f"sha256:{'9' * 64}",
        ),
        replace(
            PublicFeedActivationProjection.create(
                definition=definition,
                schedule_id=uuid4(),
                actor_ref="admin:activator",
                at=NOW + timedelta(seconds=3),
            ),
            adapter_code="kefe.public_feed.other.v1",
        ),
    ):
        repository = InMemoryPublicFeedCatalogRepository()
        repository.add_definition(definition)
        repository.add_activation(activation)
        runtime = InMemoryPublicFeedRuntimeProfileRegistry()

        with pytest.raises(
            RuntimeError,
            match="persisted public-feed activation identity drifted",
        ):
            _service(repository, runtime).rehydrate_runtime_profiles()
        assert runtime.get(definition.definition.adapter_code) is None

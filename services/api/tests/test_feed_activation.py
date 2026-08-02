from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
    STAGE_CODE,
    STAGE_VERSION,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    InMemoryIngestionWorkerRuntimeRegistry,
    IngestionRuntimePlan,
    IngestionRuntimeStage,
)
from kefe_api.modules.ingestion_orchestration.models import ExecutorKind
from kefe_api.modules.knowledge.feed_activation import (
    FeedActivationOutcome,
    FeedActivationService,
    FeedPipelineDefinition,
    FeedPipelineLifecycle,
    InMemoryFeedParserProfileRegistry,
    InMemoryFeedPipelineDefinitionRepository,
    adoption_configuration_hash,
    parser_configuration_hash,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    InMemoryProviderAdoptionRegistry,
    ProviderAdoptionProfile,
    ProviderHttpMethod,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    UnconfiguredRawSourceEvidenceStore,
)

NOW = datetime(2026, 8, 3, 3, 0, tzinfo=UTC)
FEED_CODE = "feed.example_news.v1"
ADAPTER_CODE = "provider.example_feed.v1"
FEED_URL = "https://feeds.example.test/news.xml"
CAPABILITY_REF = "evidence://capability/feed-activation-test-v1"


class CountingTransport:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        del request
        self.calls += 1
        raise AssertionError("activation preflight must not execute HTTP")


class EmptyAuthRegistry:
    def get(self, adapter_code: str):
        raise KeyError(adapter_code)


class PresentAuthRegistry:
    def get(self, adapter_code: str):
        return object()


def _adoption(
    *,
    max_response_bytes: int = 1_048_576,
) -> ProviderAdoptionProfile:
    return ProviderAdoptionProfile(
        adapter_code=ADAPTER_CODE,
        allowed_origins=("https://feeds.example.test",),
        allowed_methods=(ProviderHttpMethod.GET,),
        allowed_media_types=(
            "application/atom+xml",
            "application/rss+xml",
            "application/xml",
            "text/xml",
        ),
        connect_timeout_ms=1000,
        read_timeout_ms=2000,
        total_timeout_ms=3000,
        max_response_bytes=max_response_bytes,
        max_redirect_hops=1,
        terms_evidence_ref="evidence://terms/example-feed-v1",
        rate_limit_evidence_ref="evidence://rate/example-feed-v1",
    )


def _definition(
    adoption: ProviderAdoptionProfile,
    parser: StrictRssAtomParseProfile,
    **changes,
) -> FeedPipelineDefinition:
    values = {
        "feed_code": FEED_CODE,
        "adapter_code": ADAPTER_CODE,
        "external_locator": FEED_URL,
        "adoption_configuration_hash": adoption_configuration_hash(adoption),
        "parser_configuration_hash": parser_configuration_hash(parser),
        "extraction_pipeline_code": PIPELINE_CODE,
        "extraction_pipeline_version": PIPELINE_VERSION,
        "acquisition_configuration_hash": "sha256:" + "a" * 64,
        "interval_seconds": 300,
        "max_dispatch_attempts": 3,
        "evidence_capability_ref": CAPABILITY_REF,
        "created_at": NOW,
    }
    values.update(changes)
    return FeedPipelineDefinition.create(**values)


def _service(
    *,
    credential_mode: ProviderCredentialMode = ProviderCredentialMode.PUBLIC,
    provider_paused: bool = False,
    adoption: ProviderAdoptionProfile | None = None,
    auth_present: bool = False,
    evidence_configured: bool = True,
    runtime=None,
):
    resolved_adoption = adoption or _adoption()
    parser = StrictRssAtomParseProfile()
    definitions = InMemoryFeedPipelineDefinitionRepository()
    providers = InMemorySourceProviderAdmissionRepository()
    provider_service = SourceProviderAdmissionService(providers, clock=lambda: NOW)
    provider_service.register(
        adapter_code=ADAPTER_CODE,
        credential_mode=credential_mode,
        secret_ref=(
            None
            if credential_mode is ProviderCredentialMode.PUBLIC
            else "secret://providers/example-feed"
        ),
        quota_limit=100,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    if provider_paused:
        provider_service.pause(ADAPTER_CODE, at=NOW + timedelta(seconds=1))
    evidence = (
        InMemoryRawSourceEvidenceStore(capability_ref=CAPABILITY_REF)
        if evidence_configured
        else UnconfiguredRawSourceEvidenceStore()
    )
    transport = CountingTransport()
    processor = FeedItemExtractionStageProcessor(
        knowledge=InMemoryKnowledgeRepository(),
        evidence=evidence,
    )
    resolved_runtime = runtime or build_feed_item_extraction_runtime(processor)
    service = FeedActivationService(
        definitions=definitions,
        providers=providers,
        adoption_profiles=InMemoryProviderAdoptionRegistry((resolved_adoption,)),
        auth_profiles=PresentAuthRegistry() if auth_present else EmptyAuthRegistry(),
        evidence_store=evidence,
        parser_profiles=InMemoryFeedParserProfileRegistry((parser,)),
        public_http_factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,  # type: ignore[arg-type]
            evidence_store=evidence,
        ),
        ingestion_runtime=resolved_runtime,
    )
    definition = _definition(resolved_adoption, parser)
    return service, definitions, definition, transport, evidence, providers


def test_enable_records_exact_fingerprint_without_side_effects() -> None:
    service, repository, definition, transport, evidence, providers = _service()
    service.register(definition)

    verified = service.preflight(FEED_CODE, at=NOW + timedelta(seconds=2))
    enabled = service.enable(FEED_CODE, at=NOW + timedelta(seconds=3))

    assert verified.outcome is FeedActivationOutcome.VERIFIED
    assert verified.lifecycle_state is FeedPipelineLifecycle.DRAFT
    assert verified.dependency_fingerprint is not None
    assert enabled.outcome is FeedActivationOutcome.ENABLED
    assert enabled.lifecycle_state is FeedPipelineLifecycle.ENABLED
    assert enabled.dependency_fingerprint == verified.dependency_fingerprint
    assert enabled.verified_at == NOW + timedelta(seconds=3)
    stored = repository.get(FEED_CODE)
    assert stored is not None
    assert stored.lifecycle_state is FeedPipelineLifecycle.ENABLED
    assert transport.calls == 0
    assert evidence.object_count == 0
    assert providers._permits == {}
    operational = enabled.as_operational_dict()
    assert FEED_URL not in repr(operational)
    assert CAPABILITY_REF not in repr(operational)


def test_configuration_is_immutable_and_lifecycle_is_terminal() -> None:
    service, repository, definition, _, _, _ = _service()
    service.register(definition)
    changed = _definition(
        _adoption(),
        StrictRssAtomParseProfile(),
        interval_seconds=600,
    )
    with pytest.raises(ValueError, match="immutable"):
        service.register(changed)

    assert service.enable(FEED_CODE, at=NOW + timedelta(seconds=1)).outcome is (
        FeedActivationOutcome.ENABLED
    )
    assert service.pause(FEED_CODE, at=NOW + timedelta(seconds=2)).outcome is (
        FeedActivationOutcome.PAUSED
    )
    assert service.resume(FEED_CODE, at=NOW + timedelta(seconds=3)).outcome is (
        FeedActivationOutcome.ENABLED
    )
    assert service.retire(FEED_CODE, at=NOW + timedelta(seconds=4)).outcome is (
        FeedActivationOutcome.RETIRED
    )
    blocked = service.enable(FEED_CODE, at=NOW + timedelta(seconds=5))
    assert blocked.outcome is FeedActivationOutcome.BLOCKED
    assert blocked.reason_code == "FEED_ACTIVATION_LIFECYCLE_INVALID"
    assert repository.get(FEED_CODE).lifecycle_state is FeedPipelineLifecycle.RETIRED


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    (
        (
            {"credential_mode": ProviderCredentialMode.SECRET_REF},
            "FEED_ACTIVATION_PROVIDER_NOT_PUBLIC",
        ),
        (
            {"provider_paused": True},
            "FEED_ACTIVATION_PROVIDER_NOT_ENABLED",
        ),
        (
            {"auth_present": True},
            "FEED_ACTIVATION_AUTH_PROFILE_FORBIDDEN",
        ),
        (
            {"evidence_configured": False},
            "FEED_ACTIVATION_EVIDENCE_UNAVAILABLE",
        ),
        (
            {"runtime": InMemoryIngestionWorkerRuntimeRegistry()},
            "FEED_ACTIVATION_RUNTIME_PLAN_NOT_REGISTERED",
        ),
    ),
)
def test_preflight_dependencies_fail_closed_without_mutation(
    overrides,
    expected_code: str,
) -> None:
    service, repository, definition, transport, _, providers = _service(**overrides)
    service.register(definition)

    result = service.enable(FEED_CODE, at=NOW + timedelta(seconds=2))

    assert result.outcome is FeedActivationOutcome.BLOCKED
    assert result.reason_code == expected_code
    stored = repository.get(FEED_CODE)
    assert stored.lifecycle_state is FeedPipelineLifecycle.DRAFT
    assert stored.dependency_fingerprint is None
    assert stored.verified_at is None
    assert transport.calls == 0
    assert providers._permits == {}


def test_adoption_hash_and_evidence_capability_mismatch_fail_closed() -> None:
    service, repository, definition, _, _, _ = _service()
    mismatched = FeedPipelineDefinition.create(
        feed_code=definition.feed_code,
        adapter_code=definition.adapter_code,
        external_locator=definition.external_locator,
        adoption_configuration_hash="sha256:" + "b" * 64,
        parser_configuration_hash=definition.parser_configuration_hash,
        extraction_pipeline_code=definition.extraction_pipeline_code,
        extraction_pipeline_version=definition.extraction_pipeline_version,
        acquisition_configuration_hash=definition.acquisition_configuration_hash,
        interval_seconds=definition.interval_seconds,
        max_dispatch_attempts=definition.max_dispatch_attempts,
        evidence_capability_ref=definition.evidence_capability_ref,
        created_at=definition.created_at,
    )
    service.register(mismatched)
    result = service.enable(FEED_CODE, at=NOW + timedelta(seconds=1))
    assert result.reason_code == "FEED_ACTIVATION_ADOPTION_PROFILE_MISMATCH"
    assert repository.get(FEED_CODE).lifecycle_state is FeedPipelineLifecycle.DRAFT

    other_service, other_repo, other_definition, _, _, _ = _service()
    wrong_evidence = FeedPipelineDefinition.create(
        feed_code=other_definition.feed_code,
        adapter_code=other_definition.adapter_code,
        external_locator=other_definition.external_locator,
        adoption_configuration_hash=other_definition.adoption_configuration_hash,
        parser_configuration_hash=other_definition.parser_configuration_hash,
        extraction_pipeline_code=other_definition.extraction_pipeline_code,
        extraction_pipeline_version=other_definition.extraction_pipeline_version,
        acquisition_configuration_hash=other_definition.acquisition_configuration_hash,
        interval_seconds=other_definition.interval_seconds,
        max_dispatch_attempts=other_definition.max_dispatch_attempts,
        evidence_capability_ref="evidence://capability/wrong-v1",
        created_at=other_definition.created_at,
    )
    other_service.register(wrong_evidence)
    other = other_service.enable(FEED_CODE, at=NOW + timedelta(seconds=1))
    assert other.reason_code == "FEED_ACTIVATION_EVIDENCE_CAPABILITY_MISMATCH"
    assert other_repo.get(FEED_CODE).lifecycle_state is FeedPipelineLifecycle.DRAFT


def test_runtime_dependency_drift_is_detected_after_pause() -> None:
    service, repository, definition, _, evidence, providers = _service()
    service.register(definition)
    enabled = service.enable(FEED_CODE, at=NOW + timedelta(seconds=1))
    assert enabled.outcome is FeedActivationOutcome.ENABLED
    service.pause(FEED_CODE, at=NOW + timedelta(seconds=2))

    parser = StrictRssAtomParseProfile()
    drifted_runtime = InMemoryIngestionWorkerRuntimeRegistry(
        plans=(
            IngestionRuntimePlan(
                pipeline_code=PIPELINE_CODE,
                pipeline_version=PIPELINE_VERSION,
                stages=(
                    IngestionRuntimeStage(
                        stage_code=STAGE_CODE,
                        stage_version=STAGE_VERSION,
                        max_attempts=4,
                        executor_kind=ExecutorKind.DETERMINISTIC,
                    ),
                ),
            ),
        ),
        processors={},
    )
    drifted = FeedActivationService(
        definitions=repository,
        providers=providers,
        adoption_profiles=InMemoryProviderAdoptionRegistry((_adoption(),)),
        auth_profiles=EmptyAuthRegistry(),
        evidence_store=evidence,
        parser_profiles=InMemoryFeedParserProfileRegistry((parser,)),
        public_http_factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=CountingTransport(),  # type: ignore[arg-type]
            evidence_store=evidence,
        ),
        ingestion_runtime=drifted_runtime,
    )
    result = drifted.resume(FEED_CODE, at=NOW + timedelta(seconds=3))
    assert result.outcome is FeedActivationOutcome.BLOCKED
    assert result.reason_code == "FEED_ACTIVATION_DEPENDENCY_DRIFT"
    assert repository.get(FEED_CODE).lifecycle_state is FeedPipelineLifecycle.PAUSED

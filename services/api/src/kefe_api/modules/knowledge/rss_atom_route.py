from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from typing import Protocol

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    PROPOSAL_KIND,
    STAGE_CODE,
    STAGE_VERSION,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    InMemoryIngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_http_capture import (
    MAX_EXTERNAL_LOCATOR_CHARS,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapter,
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomCaptureDefinition,
    StrictRssAtomParseProfile,
)
from kefe_api.modules.knowledge.source_acquisition import SourceAcquisitionCommand
from kefe_api.modules.knowledge.source_evidence import (
    RawSourceEvidenceReader,
    RawSourceEvidenceStore,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

MAX_ROUTE_CONTEXT_CHARS = 64


def _optional_context(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAX_ROUTE_CONTEXT_CHARS:
        raise ValueError(f"{field_name} is invalid")
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        raise ValueError(f"{field_name} must use visible ASCII")
    return value


class ReadableRawSourceEvidenceStore(
    RawSourceEvidenceStore,
    RawSourceEvidenceReader,
    Protocol,
):
    pass


@dataclass(frozen=True, slots=True)
class RssAtomRouteProfile:
    route_code: str
    adapter_code: str
    parser_profile: StrictRssAtomParseProfile
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.route_code)
        require_versioned_adapter_code(self.adapter_code)
        if type(self.parser_profile) is not StrictRssAtomParseProfile:
            raise ValueError("route requires an exact RSS/Atom parser profile")
        if self.locale != _optional_context(self.locale, "locale"):
            raise ValueError("locale must be canonical")
        if self.jurisdiction_code != _optional_context(
            self.jurisdiction_code,
            "jurisdiction_code",
        ):
            raise ValueError("jurisdiction_code must be canonical")

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.route_code,
            self.adapter_code,
            self.parser_profile.immutable_configuration,
            self.locale,
            self.jurisdiction_code,
            PIPELINE_CODE,
            PIPELINE_VERSION,
            STAGE_CODE,
            STAGE_VERSION,
            PROPOSAL_KIND,
            PAYLOAD_SCHEMA_REF,
            PAYLOAD_SCHEMA_VERSION,
        )

    @property
    def configuration_hash(self) -> str:
        encoded = dumps(
            self.immutable_configuration,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{sha256(encoded).hexdigest()}"

    def acquisition_command(self, external_locator: str) -> SourceAcquisitionCommand:
        if (
            not external_locator
            or external_locator != external_locator.strip()
            or len(external_locator) > MAX_EXTERNAL_LOCATOR_CHARS
        ):
            raise ValueError("external_locator is invalid")
        return SourceAcquisitionCommand(
            adapter_code=self.adapter_code,
            external_locator=external_locator,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=self.configuration_hash,
            locale=self.locale,
            jurisdiction_code=self.jurisdiction_code,
        )


@dataclass(frozen=True, slots=True)
class RssAtomRouteBundle:
    profile: RssAtomRouteProfile
    capture_definition: StrictRssAtomCaptureDefinition
    public_adapter: EvidenceBackedPublicHttpCaptureAdapter
    extraction_processor: FeedItemExtractionStageProcessor
    ingestion_registry: InMemoryIngestionWorkerRuntimeRegistry

    def __post_init__(self) -> None:
        if type(self.profile) is not RssAtomRouteProfile:
            raise ValueError("route bundle requires an exact route profile")
        if type(self.capture_definition) is not StrictRssAtomCaptureDefinition:
            raise ValueError("route bundle capture definition is invalid")
        if self.capture_definition.adapter_code != self.profile.adapter_code:
            raise ValueError("route capture adapter code drifted")
        if self.capture_definition.profile is not self.profile.parser_profile:
            raise ValueError("route capture parser profile identity drifted")
        if self.public_adapter.adapter_code != self.profile.adapter_code:
            raise ValueError("route public adapter code drifted")
        if getattr(self.extraction_processor, "_profile", None) is not (
            self.profile.parser_profile
        ):
            raise ValueError("route extraction parser profile identity drifted")

        try:
            plan = self.ingestion_registry.get_plan(
                pipeline_code=PIPELINE_CODE,
                pipeline_version=PIPELINE_VERSION,
            )
            processor = self.ingestion_registry.get_processor(
                pipeline_code=PIPELINE_CODE,
                pipeline_version=PIPELINE_VERSION,
                stage_code=STAGE_CODE,
                stage_version=STAGE_VERSION,
            )
        except KeyError as exc:
            raise ValueError("route ingestion runtime is incomplete") from exc
        if len(plan.stages) != 1 or plan.stages[0].identity != (
            STAGE_CODE,
            STAGE_VERSION,
        ):
            raise ValueError("route ingestion plan identity drifted")
        if processor is not self.extraction_processor:
            raise ValueError("route extraction processor registration drifted")

    @property
    def route_code(self) -> str:
        return self.profile.route_code

    @property
    def adapter_code(self) -> str:
        return self.profile.adapter_code

    def acquisition_command(self, external_locator: str) -> SourceAcquisitionCommand:
        return self.profile.acquisition_command(external_locator)


class RssAtomRouteFactory:
    def __init__(
        self,
        *,
        transport: ControlledProviderHttpTransport,
        evidence_store: ReadableRawSourceEvidenceStore,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        if not callable(getattr(evidence_store, "seal", None)) or not callable(
            getattr(evidence_store, "read", None)
        ):
            raise ValueError("route evidence store must support seal and read")
        self._capture_factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,
            evidence_store=evidence_store,
        )
        self._evidence_store = evidence_store
        self._knowledge_repository = knowledge_repository

    def build(self, profile: RssAtomRouteProfile) -> RssAtomRouteBundle:
        if type(profile) is not RssAtomRouteProfile:
            raise ValueError("route factory requires an exact route profile")
        definition = StrictRssAtomCaptureDefinition(
            adapter_code=profile.adapter_code,
            profile=profile.parser_profile,
        )
        public_adapter = self._capture_factory.create(definition)
        extraction_processor = FeedItemExtractionStageProcessor(
            knowledge=self._knowledge_repository,
            evidence=self._evidence_store,
            profile=profile.parser_profile,
        )
        ingestion_registry = build_feed_item_extraction_runtime(
            extraction_processor
        )
        return RssAtomRouteBundle(
            profile=profile,
            capture_definition=definition,
            public_adapter=public_adapter,
            extraction_processor=extraction_processor,
            ingestion_registry=ingestion_registry,
        )


class RssAtomRouteRegistry(Protocol):
    def get(self, route_code: str) -> RssAtomRouteBundle: ...

    def get_by_adapter_code(self, adapter_code: str) -> RssAtomRouteBundle: ...


class InMemoryRssAtomRouteRegistry:
    def __init__(self, routes: tuple[RssAtomRouteBundle, ...] = ()) -> None:
        by_route: dict[str, RssAtomRouteBundle] = {}
        by_adapter: dict[str, RssAtomRouteBundle] = {}
        for route in routes:
            if type(route) is not RssAtomRouteBundle:
                raise ValueError("route registry requires exact route bundles")
            if route.route_code in by_route:
                raise ValueError("duplicate RSS/Atom route code")
            if route.adapter_code in by_adapter:
                raise ValueError("duplicate RSS/Atom route adapter code")
            by_route[route.route_code] = route
            by_adapter[route.adapter_code] = route
        self._by_route = MappingProxyType(by_route)
        self._by_adapter = MappingProxyType(by_adapter)

    def get(self, route_code: str) -> RssAtomRouteBundle:
        require_versioned_adapter_code(route_code)
        try:
            return self._by_route[route_code]
        except KeyError as exc:
            raise KeyError("RSS_ATOM_ROUTE_NOT_REGISTERED") from exc

    def get_by_adapter_code(self, adapter_code: str) -> RssAtomRouteBundle:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._by_adapter[adapter_code]
        except KeyError as exc:
            raise KeyError("RSS_ATOM_ROUTE_NOT_REGISTERED") from exc

    @property
    def route_count(self) -> int:
        return len(self._by_route)


__all__ = [
    "InMemoryRssAtomRouteRegistry",
    "ReadableRawSourceEvidenceStore",
    "RssAtomRouteBundle",
    "RssAtomRouteFactory",
    "RssAtomRouteProfile",
    "RssAtomRouteRegistry",
]

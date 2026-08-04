from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from typing import Protocol
from urllib.parse import parse_qsl, urlsplit

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    InMemoryProviderAdoptionRegistry,
    ProviderAdoptionProfile,
    ProviderAdoptionRegistry,
    ProviderHttpMethod,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    InMemoryPublicSourceCaptureRegistry,
    PublicSourceCaptureRegistry,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomCaptureDefinition,
    StrictRssAtomParseProfile,
)
from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionCommand,
    SourceAcquisitionResult,
)
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceReader
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

MAX_FEED_CODE_CHARS = 128
MAX_DISPLAY_NAME_CHARS = 160
MAX_EXTERNAL_LOCATOR_CHARS = 4096
MAX_OPTIONAL_CODE_CHARS = 32

_FORBIDDEN_QUERY_NAMES = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "key",
        "password",
        "secret",
        "sig",
        "signature",
        "token",
    }
)
_ERROR_CODE = re.compile(r"^PUBLIC_FEED_[A-Z0-9_]{1,80}$")


def _require_exact_text(value: str, field_name: str, max_chars: int) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be exact nonblank text")
    if len(value) > max_chars:
        raise ValueError(f"{field_name} exceeds the supported length")


def _canonical_locator(value: str) -> tuple[str, str]:
    _require_exact_text(value, "external_locator", MAX_EXTERNAL_LOCATOR_CHARS)
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("external_locator is invalid") from exc
    if parsed.scheme != "https":
        raise ValueError("external_locator must use https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("external_locator cannot contain userinfo")
    if parsed.hostname is None:
        raise ValueError("external_locator requires a hostname")
    try:
        parsed.hostname.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("external_locator hostname must be ASCII") from exc
    if parsed.hostname != parsed.hostname.lower():
        raise ValueError("external_locator hostname must be lowercase")
    if port not in (None, 443):
        raise ValueError("external_locator port must be 443")
    if parsed.fragment:
        raise ValueError("external_locator cannot contain a fragment")
    for name, _ in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = name.strip().lower().replace("-", "_")
        if normalized in _FORBIDDEN_QUERY_NAMES:
            raise ValueError("external_locator contains a sensitive query name")
    rendered_host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    origin = f"https://{rendered_host}"
    return value, origin


def _optional_code(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _require_exact_text(value, field_name, MAX_OPTIONAL_CODE_CHARS)


class PublicFeedRuntimeError(Exception):
    def __init__(self, code: str) -> None:
        if _ERROR_CODE.fullmatch(code) is None:
            raise ValueError("public feed runtime error code is invalid")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"PublicFeedRuntimeError(code={self.code!r})"


@dataclass(frozen=True, slots=True)
class PublicProviderCapabilityTemplate:
    adapter_code: str
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int

    def instantiate(self, *, created_at: datetime) -> SourceProviderCapability:
        return SourceProviderCapability.create(
            adapter_code=self.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=self.quota_limit,
            quota_window_seconds=self.quota_window_seconds,
            failure_threshold=self.failure_threshold,
            circuit_open_seconds=self.circuit_open_seconds,
            permit_ttl_seconds=self.permit_ttl_seconds,
            created_at=created_at,
        )


@dataclass(frozen=True, slots=True)
class PublicFeedDefinition:
    feed_code: str
    display_name: str
    adapter_code: str
    external_locator: str
    parser_profile: StrictRssAtomParseProfile
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_response_bytes: int
    max_redirect_hops: int
    terms_evidence_ref: str
    rate_limit_evidence_ref: str
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    language_code: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        _require_exact_text(self.feed_code, "feed_code", MAX_FEED_CODE_CHARS)
        _require_exact_text(
            self.display_name,
            "display_name",
            MAX_DISPLAY_NAME_CHARS,
        )
        canonical_locator, _ = _canonical_locator(self.external_locator)
        if canonical_locator != self.external_locator:
            raise ValueError("external_locator must be canonical")
        if type(self.parser_profile) is not StrictRssAtomParseProfile:
            raise ValueError("parser_profile must be exact StrictRssAtomParseProfile")
        if self.max_response_bytes < self.parser_profile.max_document_bytes:
            raise ValueError("HTTP response budget cannot be below parser byte budget")
        _optional_code(self.language_code, "language_code")
        _optional_code(self.jurisdiction_code, "jurisdiction_code")
        self.to_adoption_profile()
        self.capability_template.instantiate(created_at=datetime(2026, 1, 1, tzinfo=UTC))

    @property
    def origin(self) -> str:
        return _canonical_locator(self.external_locator)[1]

    @property
    def capability_template(self) -> PublicProviderCapabilityTemplate:
        return PublicProviderCapabilityTemplate(
            adapter_code=self.adapter_code,
            quota_limit=self.quota_limit,
            quota_window_seconds=self.quota_window_seconds,
            failure_threshold=self.failure_threshold,
            circuit_open_seconds=self.circuit_open_seconds,
            permit_ttl_seconds=self.permit_ttl_seconds,
        )

    @property
    def configuration_hash(self) -> str:
        payload = {
            "feed_code": self.feed_code,
            "display_name": self.display_name,
            "adapter_code": self.adapter_code,
            "external_locator": self.external_locator,
            "parser_profile": self.parser_profile.immutable_configuration,
            "http": (
                self.connect_timeout_ms,
                self.read_timeout_ms,
                self.total_timeout_ms,
                self.max_response_bytes,
                self.max_redirect_hops,
                self.terms_evidence_ref,
                self.rate_limit_evidence_ref,
            ),
            "admission": (
                self.quota_limit,
                self.quota_window_seconds,
                self.failure_threshold,
                self.circuit_open_seconds,
                self.permit_ttl_seconds,
            ),
            "language_code": self.language_code,
            "jurisdiction_code": self.jurisdiction_code,
            "pipeline": (PIPELINE_CODE, PIPELINE_VERSION),
        }
        encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return f"sha256:{sha256(encoded).hexdigest()}"

    def to_adoption_profile(self) -> ProviderAdoptionProfile:
        return ProviderAdoptionProfile(
            adapter_code=self.adapter_code,
            allowed_origins=(self.origin,),
            allowed_methods=(ProviderHttpMethod.GET,),
            allowed_media_types=self.parser_profile.accepted_media_types,
            connect_timeout_ms=self.connect_timeout_ms,
            read_timeout_ms=self.read_timeout_ms,
            total_timeout_ms=self.total_timeout_ms,
            max_response_bytes=self.max_response_bytes,
            max_redirect_hops=self.max_redirect_hops,
            terms_evidence_ref=self.terms_evidence_ref,
            rate_limit_evidence_ref=self.rate_limit_evidence_ref,
        )

    def acquisition_command(self) -> SourceAcquisitionCommand:
        return SourceAcquisitionCommand(
            adapter_code=self.adapter_code,
            external_locator=self.external_locator,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=self.configuration_hash,
            locale=self.language_code,
            jurisdiction_code=self.jurisdiction_code,
        )


class PublicFeedDefinitionRegistry(Protocol):
    def get(self, feed_code: str) -> PublicFeedDefinition: ...


class InMemoryPublicFeedDefinitionRegistry:
    def __init__(self, definitions: tuple[PublicFeedDefinition, ...] = ()) -> None:
        expected_order = tuple(sorted(definitions, key=lambda item: item.feed_code))
        if definitions != expected_order:
            raise ValueError("public feed definitions must be sorted by feed_code")
        by_feed: dict[str, PublicFeedDefinition] = {}
        adapter_codes: set[str] = set()
        for definition in definitions:
            if definition.feed_code in by_feed:
                raise ValueError("duplicate public feed code")
            if definition.adapter_code in adapter_codes:
                raise ValueError("duplicate public feed adapter code")
            by_feed[definition.feed_code] = definition
            adapter_codes.add(definition.adapter_code)
        self._definitions = MappingProxyType(by_feed)

    def get(self, feed_code: str) -> PublicFeedDefinition:
        _require_exact_text(feed_code, "feed_code", MAX_FEED_CODE_CHARS)
        try:
            return self._definitions[feed_code]
        except KeyError as exc:
            raise KeyError(feed_code) from exc

    @property
    def definitions(self) -> tuple[PublicFeedDefinition, ...]:
        return tuple(self._definitions.values())


@dataclass(frozen=True, slots=True)
class PublicFeedRuntimeBundle:
    definitions: InMemoryPublicFeedDefinitionRegistry
    adoption_registry: ProviderAdoptionRegistry
    capture_registry: PublicSourceCaptureRegistry
    ingestion_registry: IngestionWorkerRuntimeRegistry
    capability_templates: tuple[PublicProviderCapabilityTemplate, ...]


class PublicFeedAcquisition(Protocol):
    def acquire(
        self,
        command: SourceAcquisitionCommand,
        *,
        trace_id: str | None = None,
    ) -> SourceAcquisitionResult: ...


class ManualPublicFeedCaptureService:
    def __init__(
        self,
        *,
        definitions: PublicFeedDefinitionRegistry,
        acquisition: PublicFeedAcquisition,
    ) -> None:
        self._definitions = definitions
        self._acquisition = acquisition

    def capture_once(
        self,
        *,
        feed_code: str,
        trace_id: str | None = None,
    ) -> SourceAcquisitionResult:
        try:
            definition = self._definitions.get(feed_code)
        except (KeyError, ValueError) as exc:
            raise PublicFeedRuntimeError("PUBLIC_FEED_DEFINITION_NOT_FOUND") from exc
        try:
            return self._acquisition.acquire(
                definition.acquisition_command(),
                trace_id=trace_id,
            )
        except PublicFeedRuntimeError:
            raise
        except Exception as exc:
            raise PublicFeedRuntimeError("PUBLIC_FEED_CAPTURE_UNEXPECTED") from exc


def build_public_feed_runtime_bundle(
    *,
    definitions: tuple[PublicFeedDefinition, ...],
    adapter_factory: EvidenceBackedPublicHttpCaptureAdapterFactory,
    knowledge: KnowledgeRepository,
    evidence: RawSourceEvidenceReader,
) -> PublicFeedRuntimeBundle:
    if not definitions:
        raise ValueError("at least one public feed definition is required")
    registry = InMemoryPublicFeedDefinitionRegistry(definitions)
    adoption_profiles = tuple(
        sorted(
            (definition.to_adoption_profile() for definition in definitions),
            key=lambda item: item.adapter_code,
        )
    )
    adapters = tuple(
        sorted(
            (
                adapter_factory.create(
                    StrictRssAtomCaptureDefinition(
                        adapter_code=definition.adapter_code,
                        profile=definition.parser_profile,
                    )
                )
                for definition in definitions
            ),
            key=lambda item: item.adapter_code,
        )
    )
    extraction_processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )
    return PublicFeedRuntimeBundle(
        definitions=registry,
        adoption_registry=InMemoryProviderAdoptionRegistry(adoption_profiles),
        capture_registry=InMemoryPublicSourceCaptureRegistry(adapters),
        ingestion_registry=build_feed_item_extraction_runtime(extraction_processor),
        capability_templates=tuple(definition.capability_template for definition in definitions),
    )


__all__ = [
    "InMemoryPublicFeedDefinitionRegistry",
    "ManualPublicFeedCaptureService",
    "PublicFeedDefinition",
    "PublicFeedDefinitionRegistry",
    "PublicFeedRuntimeBundle",
    "PublicFeedRuntimeError",
    "PublicProviderCapabilityTemplate",
    "build_public_feed_runtime_bundle",
]

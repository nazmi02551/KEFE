from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from time import monotonic_ns
from types import MappingProxyType
from typing import Protocol
from urllib.parse import parse_qsl, urlsplit

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    MAX_PROPOSALS,
    PIPELINE_CODE,
    PIPELINE_VERSION,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCapabilityLifecycle,
    ProviderCircuitState,
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    InMemoryProviderAdoptionRegistry,
    PinnedHttpBackend,
    ProviderAdoptionProfile,
    ProviderAdoptionRegistry,
    ProviderDnsResolver,
    ProviderHttpMethod,
    ProviderHttpObserver,
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
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceStore
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code
from kefe_api.modules.knowledge.source_scheduler import (
    MAXIMUM_DISPATCH_ATTEMPTS,
    MAXIMUM_INTERVAL_SECONDS,
    MINIMUM_DISPATCH_ATTEMPTS,
    MINIMUM_INTERVAL_SECONDS,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceAcquisitionSchedulerService,
)

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


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _canonical_optional(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must not be blank or padded")
    return value


def _canonical_feed_origin(value: str) -> str:
    if not value or value != value.strip() or len(value) > 4096:
        raise ValueError("external_locator must be bounded exact text")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("external_locator is invalid") from exc
    if parsed.scheme != "https":
        raise ValueError("external_locator must use https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("external_locator cannot contain userinfo")
    if parsed.hostname is None or parsed.fragment:
        raise ValueError("external_locator requires a host and no fragment")
    try:
        parsed.hostname.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("external_locator hostname must be ASCII") from exc
    if "*" in parsed.hostname or port not in (None, 443):
        raise ValueError("external_locator host or port is invalid")
    for query_name, _ in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = query_name.strip().lower().replace("-", "_")
        if normalized in _FORBIDDEN_QUERY_NAMES:
            raise ValueError("credential-like query parameter is forbidden")
    host = parsed.hostname.lower()
    rendered_host = f"[{host}]" if ":" in host else host
    return f"https://{rendered_host}"


def _configuration_hash(payload: dict[str, object]) -> str:
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


@dataclass(frozen=True, slots=True)
class PublicFeedScheduleSeed:
    activation_code: str
    adapter_code: str
    external_locator: str
    configuration_hash: str
    first_due_at: datetime
    interval_seconds: int
    max_dispatch_attempts: int
    taxonomy_version: str | None = None
    methodology_version: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.activation_code)
        require_versioned_adapter_code(self.adapter_code)
        if not self.configuration_hash.startswith("sha256:") or len(
            self.configuration_hash
        ) != 71:
            raise ValueError("configuration_hash must be canonical SHA-256")
        _canonical_feed_origin(self.external_locator)
        _require_utc(self.first_due_at, "first_due_at")
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")
        for value, field_name in (
            (self.taxonomy_version, "taxonomy_version"),
            (self.methodology_version, "methodology_version"),
            (self.locale, "locale"),
            (self.jurisdiction_code, "jurisdiction_code"),
        ):
            _canonical_optional(value, field_name)

    def install(
        self,
        scheduler: SourceAcquisitionSchedulerService,
        *,
        now: datetime | None = None,
    ):
        return scheduler.create_schedule(
            adapter_code=self.adapter_code,
            external_locator=self.external_locator,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=self.configuration_hash,
            first_due_at=self.first_due_at,
            interval_seconds=self.interval_seconds,
            max_dispatch_attempts=self.max_dispatch_attempts,
            taxonomy_version=self.taxonomy_version,
            methodology_version=self.methodology_version,
            locale=self.locale,
            jurisdiction_code=self.jurisdiction_code,
            now=now,
        )


@dataclass(frozen=True, slots=True)
class PublicFeedActivationDefinition:
    activation_code: str
    adapter_code: str
    external_locator: str
    adoption_profile: ProviderAdoptionProfile
    parser_profile: StrictRssAtomParseProfile
    capability: SourceProviderCapability
    first_due_at: datetime
    interval_seconds: int
    max_dispatch_attempts: int
    taxonomy_version: str | None = None
    methodology_version: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.activation_code)
        require_versioned_adapter_code(self.adapter_code)
        if type(self.adoption_profile) is not ProviderAdoptionProfile:
            raise ValueError("adoption_profile must be exact ProviderAdoptionProfile")
        if type(self.parser_profile) is not StrictRssAtomParseProfile:
            raise ValueError("parser_profile must be exact StrictRssAtomParseProfile")
        if type(self.capability) is not SourceProviderCapability:
            raise ValueError("capability must be exact SourceProviderCapability")
        if (
            self.adoption_profile.adapter_code != self.adapter_code
            or self.capability.adapter_code != self.adapter_code
        ):
            raise ValueError("activation adapter identity mismatch")

        origin = _canonical_feed_origin(self.external_locator)
        StrictRssAtomCaptureDefinition(
            adapter_code=self.adapter_code,
            profile=self.parser_profile,
        ).build_plan(
            external_locator=self.external_locator,
            trace_id="activation-validation",
            at=self.first_due_at,
        )
        if self.adoption_profile.allowed_origins != (origin,):
            raise ValueError("activation requires one exact feed origin")
        if self.adoption_profile.allowed_methods != (ProviderHttpMethod.GET,):
            raise ValueError("public feed activation must be GET-only")
        if (
            self.adoption_profile.allowed_media_types
            != self.parser_profile.accepted_media_types
        ):
            raise ValueError("HTTP and parser media types must match exactly")
        if (
            self.adoption_profile.max_response_bytes
            != self.parser_profile.max_document_bytes
        ):
            raise ValueError("HTTP and parser byte budgets must match exactly")
        if self.parser_profile.max_items > MAX_PROPOSALS:
            raise ValueError("parser item budget exceeds feed proposal budget")

        if self.capability.credential_mode is not ProviderCredentialMode.PUBLIC:
            raise ValueError("public feed capability must use PUBLIC mode")
        if self.capability.secret_ref is not None:
            raise ValueError("public feed capability cannot contain secret_ref")
        if self.capability.lifecycle_state is not ProviderCapabilityLifecycle.ENABLED:
            raise ValueError("public feed capability must start ENABLED")
        if (
            self.capability.window_request_count != 0
            or self.capability.consecutive_failure_count != 0
            or self.capability.circuit_state is not ProviderCircuitState.CLOSED
            or self.capability.circuit_opened_at is not None
        ):
            raise ValueError("public feed capability must start clean")
        if (
            self.capability.window_started_at != self.capability.created_at
            or self.capability.updated_at != self.capability.created_at
        ):
            raise ValueError("public feed capability initial timestamps drifted")

        _require_utc(self.first_due_at, "first_due_at")
        if self.first_due_at < self.capability.created_at:
            raise ValueError("first_due_at cannot predate capability creation")
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")
        for value, field_name in (
            (self.taxonomy_version, "taxonomy_version"),
            (self.methodology_version, "methodology_version"),
            (self.locale, "locale"),
            (self.jurisdiction_code, "jurisdiction_code"),
        ):
            _canonical_optional(value, field_name)

    @property
    def configuration_payload(self) -> dict[str, object]:
        profile = self.adoption_profile
        parser = self.parser_profile
        capability = self.capability
        return {
            "activation_code": self.activation_code,
            "adapter_code": self.adapter_code,
            "external_locator": self.external_locator,
            "adoption_profile": {
                "allowed_origins": profile.allowed_origins,
                "allowed_methods": tuple(item.value for item in profile.allowed_methods),
                "allowed_media_types": profile.allowed_media_types,
                "connect_timeout_ms": profile.connect_timeout_ms,
                "read_timeout_ms": profile.read_timeout_ms,
                "total_timeout_ms": profile.total_timeout_ms,
                "max_response_bytes": profile.max_response_bytes,
                "max_redirect_hops": profile.max_redirect_hops,
                "terms_evidence_ref": profile.terms_evidence_ref,
                "rate_limit_evidence_ref": profile.rate_limit_evidence_ref,
            },
            "parser_profile": {
                "accepted_media_types": parser.accepted_media_types,
                "max_document_bytes": parser.max_document_bytes,
                "max_elements": parser.max_elements,
                "max_depth": parser.max_depth,
                "max_items": parser.max_items,
                "max_node_text_chars": parser.max_node_text_chars,
                "max_total_text_chars": parser.max_total_text_chars,
                "max_attributes_per_element": parser.max_attributes_per_element,
                "max_total_attribute_chars": parser.max_total_attribute_chars,
                "max_metadata_field_chars": parser.max_metadata_field_chars,
            },
            "capability": {
                "credential_mode": capability.credential_mode.value,
                "secret_ref": capability.secret_ref,
                "lifecycle_state": capability.lifecycle_state.value,
                "quota_limit": capability.quota_limit,
                "quota_window_seconds": capability.quota_window_seconds,
                "failure_threshold": capability.failure_threshold,
                "circuit_open_seconds": capability.circuit_open_seconds,
                "permit_ttl_seconds": capability.permit_ttl_seconds,
                "created_at": capability.created_at.isoformat(),
            },
            "schedule": {
                "pipeline_code": PIPELINE_CODE,
                "pipeline_version": PIPELINE_VERSION,
                "first_due_at": self.first_due_at.isoformat(),
                "interval_seconds": self.interval_seconds,
                "max_dispatch_attempts": self.max_dispatch_attempts,
                "taxonomy_version": self.taxonomy_version,
                "methodology_version": self.methodology_version,
                "locale": self.locale,
                "jurisdiction_code": self.jurisdiction_code,
            },
        }

    @property
    def configuration_hash(self) -> str:
        return _configuration_hash(self.configuration_payload)

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.activation_code,
            self.adapter_code,
            self.configuration_hash,
        )

    def capture_definition(self) -> StrictRssAtomCaptureDefinition:
        return StrictRssAtomCaptureDefinition(
            adapter_code=self.adapter_code,
            profile=self.parser_profile,
        )

    def schedule_seed(self) -> PublicFeedScheduleSeed:
        return PublicFeedScheduleSeed(
            activation_code=self.activation_code,
            adapter_code=self.adapter_code,
            external_locator=self.external_locator,
            configuration_hash=self.configuration_hash,
            first_due_at=self.first_due_at,
            interval_seconds=self.interval_seconds,
            max_dispatch_attempts=self.max_dispatch_attempts,
            taxonomy_version=self.taxonomy_version,
            methodology_version=self.methodology_version,
            locale=self.locale,
            jurisdiction_code=self.jurisdiction_code,
        )


class PublicFeedActivationRegistry(Protocol):
    def get(self, activation_code: str) -> PublicFeedActivationDefinition: ...

    def get_by_adapter(self, adapter_code: str) -> PublicFeedActivationDefinition: ...


class InMemoryPublicFeedActivationRegistry:
    def __init__(
        self,
        definitions: tuple[PublicFeedActivationDefinition, ...] = (),
    ) -> None:
        by_activation: dict[str, PublicFeedActivationDefinition] = {}
        by_adapter: dict[str, PublicFeedActivationDefinition] = {}
        for definition in definitions:
            existing = by_activation.get(definition.activation_code)
            if existing is not None:
                if existing.immutable_configuration != definition.immutable_configuration:
                    raise ValueError("conflicting public feed activation")
                raise ValueError("duplicate public feed activation")
            if definition.adapter_code in by_adapter:
                raise ValueError("duplicate public feed adapter activation")
            by_activation[definition.activation_code] = definition
            by_adapter[definition.adapter_code] = definition
        self._by_activation = MappingProxyType(by_activation)
        self._by_adapter = MappingProxyType(by_adapter)

    def get(self, activation_code: str) -> PublicFeedActivationDefinition:
        require_versioned_adapter_code(activation_code)
        try:
            return self._by_activation[activation_code]
        except KeyError as exc:
            raise KeyError(activation_code) from exc

    def get_by_adapter(self, adapter_code: str) -> PublicFeedActivationDefinition:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._by_adapter[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc


@dataclass(frozen=True, slots=True)
class PublicFeedActivationBundle:
    activation_registry: PublicFeedActivationRegistry
    adoption_registry: ProviderAdoptionRegistry
    public_capture_registry: PublicSourceCaptureRegistry
    provider_http_transport: ControlledProviderHttpTransport
    capabilities: tuple[SourceProviderCapability, ...]
    schedule_seeds: tuple[PublicFeedScheduleSeed, ...]


class PublicFeedActivationBundleFactory:
    def __init__(
        self,
        *,
        dns_resolver: ProviderDnsResolver,
        backend: PinnedHttpBackend,
        observer: ProviderHttpObserver,
        evidence_store: RawSourceEvidenceStore,
        monotonic_clock=monotonic_ns,
    ) -> None:
        self._dns_resolver = dns_resolver
        self._backend = backend
        self._observer = observer
        self._evidence_store = evidence_store
        self._monotonic_clock = monotonic_clock

    def build(
        self,
        definitions: tuple[PublicFeedActivationDefinition, ...] = (),
    ) -> PublicFeedActivationBundle:
        ordered = tuple(sorted(definitions, key=lambda item: item.activation_code))
        activation_registry = InMemoryPublicFeedActivationRegistry(ordered)
        adoption_registry = InMemoryProviderAdoptionRegistry(
            tuple(item.adoption_profile for item in ordered)
        )
        transport = ControlledProviderHttpTransport(
            adoption_registry=adoption_registry,
            dns_resolver=self._dns_resolver,
            backend=self._backend,
            observer=self._observer,
            monotonic_clock=self._monotonic_clock,
        )
        adapter_factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,
            evidence_store=self._evidence_store,
        )
        adapters = tuple(
            adapter_factory.create(item.capture_definition())
            for item in ordered
        )
        public_capture_registry = InMemoryPublicSourceCaptureRegistry(adapters)
        return PublicFeedActivationBundle(
            activation_registry=activation_registry,
            adoption_registry=adoption_registry,
            public_capture_registry=public_capture_registry,
            provider_http_transport=transport,
            capabilities=tuple(item.capability for item in ordered),
            schedule_seeds=tuple(item.schedule_seed() for item in ordered),
        )


__all__ = [
    "InMemoryPublicFeedActivationRegistry",
    "PublicFeedActivationBundle",
    "PublicFeedActivationBundleFactory",
    "PublicFeedActivationDefinition",
    "PublicFeedActivationRegistry",
    "PublicFeedScheduleSeed",
]

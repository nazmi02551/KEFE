from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from urllib.parse import parse_qsl, urlsplit

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
    STAGE_CODE,
    STAGE_VERSION,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRuntimeRegistry,
    InMemoryIngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_control import (
    MAXIMUM_CIRCUIT_OPEN_SECONDS,
    MAXIMUM_FAILURE_THRESHOLD,
    MAXIMUM_PERMIT_TTL_SECONDS,
    MAXIMUM_QUOTA_LIMIT,
    MAXIMUM_QUOTA_WINDOW_SECONDS,
    MINIMUM_CIRCUIT_OPEN_SECONDS,
    MINIMUM_FAILURE_THRESHOLD,
    MINIMUM_PERMIT_TTL_SECONDS,
    MINIMUM_QUOTA_LIMIT,
    MINIMUM_QUOTA_WINDOW_SECONDS,
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    MAX_CONNECT_OR_READ_TIMEOUT_MS,
    MAX_REDIRECT_HOPS,
    MAX_TOTAL_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
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
    require_versioned_adapter_code,
)
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceReader
from kefe_api.modules.knowledge.source_scheduler import (
    MAXIMUM_DISPATCH_ATTEMPTS,
    MAXIMUM_INTERVAL_SECONDS,
    MINIMUM_DISPATCH_ATTEMPTS,
    MINIMUM_INTERVAL_SECONDS,
    SourceAcquisitionSchedule,
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

RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE = StrictRssAtomParseProfile()


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _require_optional_text(value: str | None, field_name: str) -> None:
    if value is not None and (not value or value != value.strip()):
        raise ValueError(f"{field_name} must be exact nonblank text")


def _normalized_query_name(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _validate_locator(value: str) -> tuple[str, str]:
    if not value or value != value.strip() or len(value) > 4096:
        raise ValueError("external_locator must be exact bounded text")
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
    hostname = parsed.hostname.lower()
    if "*" in hostname:
        raise ValueError("external_locator hostname cannot contain wildcards")
    if port is not None:
        raise ValueError("external_locator must omit an explicit port")
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    if parsed.netloc != rendered_host:
        raise ValueError("external_locator hostname must be canonical lowercase")

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query_names = tuple(_normalized_query_name(name) for name, _ in query_pairs)
    if any(name in _FORBIDDEN_QUERY_NAMES for name in query_names):
        raise ValueError("external_locator query contains a credential-like field")
    if len(query_names) != len(set(query_names)):
        raise ValueError("external_locator query names must be unique")
    if query_pairs != sorted(query_pairs):
        raise ValueError("external_locator query parameters must be sorted")
    return value, f"https://{rendered_host}"


@dataclass(frozen=True, slots=True)
class RssAtomSubscriptionManifest:
    subscription_code: str
    adapter_code: str
    external_locator: str
    interval_seconds: int
    max_dispatch_attempts: int
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_redirect_hops: int
    terms_evidence_ref: str
    rate_limit_evidence_ref: str
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.subscription_code)
        require_versioned_adapter_code(self.adapter_code)
        canonical_locator, _ = _validate_locator(self.external_locator)
        if canonical_locator != self.external_locator:
            raise ValueError("external_locator must be canonical")
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")
        if not MINIMUM_QUOTA_LIMIT <= self.quota_limit <= MAXIMUM_QUOTA_LIMIT:
            raise ValueError("quota_limit is outside the supported range")
        if not (
            MINIMUM_QUOTA_WINDOW_SECONDS
            <= self.quota_window_seconds
            <= MAXIMUM_QUOTA_WINDOW_SECONDS
        ):
            raise ValueError("quota_window_seconds is outside the supported range")
        if not (
            MINIMUM_FAILURE_THRESHOLD
            <= self.failure_threshold
            <= MAXIMUM_FAILURE_THRESHOLD
        ):
            raise ValueError("failure_threshold is outside the supported range")
        if not (
            MINIMUM_CIRCUIT_OPEN_SECONDS
            <= self.circuit_open_seconds
            <= MAXIMUM_CIRCUIT_OPEN_SECONDS
        ):
            raise ValueError("circuit_open_seconds is outside the supported range")
        if not (
            MINIMUM_PERMIT_TTL_SECONDS
            <= self.permit_ttl_seconds
            <= MAXIMUM_PERMIT_TTL_SECONDS
        ):
            raise ValueError("permit_ttl_seconds is outside the supported range")
        for value, field_name in (
            (self.connect_timeout_ms, "connect_timeout_ms"),
            (self.read_timeout_ms, "read_timeout_ms"),
        ):
            if not MIN_TIMEOUT_MS <= value <= MAX_CONNECT_OR_READ_TIMEOUT_MS:
                raise ValueError(f"{field_name} is outside the supported range")
        if not MIN_TIMEOUT_MS <= self.total_timeout_ms <= MAX_TOTAL_TIMEOUT_MS:
            raise ValueError("total_timeout_ms is outside the supported range")
        if self.total_timeout_ms < max(self.connect_timeout_ms, self.read_timeout_ms):
            raise ValueError("total_timeout_ms cannot be below connect/read timeout")
        if not 0 <= self.max_redirect_hops <= MAX_REDIRECT_HOPS:
            raise ValueError("max_redirect_hops is outside the supported range")
        for value, field_name in (
            (self.terms_evidence_ref, "terms_evidence_ref"),
            (self.rate_limit_evidence_ref, "rate_limit_evidence_ref"),
        ):
            if not value or value != value.strip():
                raise ValueError(f"{field_name} must be exact nonblank text")
        _require_optional_text(self.locale, "locale")
        _require_optional_text(self.jurisdiction_code, "jurisdiction_code")

        self.provider_adoption_profile((self.origin,))
        SourceProviderCapability.create(
            adapter_code=self.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=self.quota_limit,
            quota_window_seconds=self.quota_window_seconds,
            failure_threshold=self.failure_threshold,
            circuit_open_seconds=self.circuit_open_seconds,
            permit_ttl_seconds=self.permit_ttl_seconds,
            created_at=datetime(2000, 1, 1, tzinfo=UTC),
        )

    @property
    def origin(self) -> str:
        return _validate_locator(self.external_locator)[1]

    @property
    def adapter_policy(self) -> tuple[object, ...]:
        return (
            self.quota_limit,
            self.quota_window_seconds,
            self.failure_threshold,
            self.circuit_open_seconds,
            self.permit_ttl_seconds,
            self.connect_timeout_ms,
            self.read_timeout_ms,
            self.total_timeout_ms,
            self.max_redirect_hops,
            self.terms_evidence_ref,
            self.rate_limit_evidence_ref,
        )

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.subscription_code,
            self.adapter_code,
            self.external_locator,
            self.interval_seconds,
            self.max_dispatch_attempts,
            *self.adapter_policy,
            self.locale,
            self.jurisdiction_code,
        )

    @property
    def configuration_hash(self) -> str:
        payload = {
            "subscription_code": self.subscription_code,
            "adapter_code": self.adapter_code,
            "external_locator": self.external_locator,
            "interval_seconds": self.interval_seconds,
            "max_dispatch_attempts": self.max_dispatch_attempts,
            "quota_limit": self.quota_limit,
            "quota_window_seconds": self.quota_window_seconds,
            "failure_threshold": self.failure_threshold,
            "circuit_open_seconds": self.circuit_open_seconds,
            "permit_ttl_seconds": self.permit_ttl_seconds,
            "connect_timeout_ms": self.connect_timeout_ms,
            "read_timeout_ms": self.read_timeout_ms,
            "total_timeout_ms": self.total_timeout_ms,
            "max_redirect_hops": self.max_redirect_hops,
            "terms_evidence_ref": self.terms_evidence_ref,
            "rate_limit_evidence_ref": self.rate_limit_evidence_ref,
            "locale": self.locale,
            "jurisdiction_code": self.jurisdiction_code,
            "parser_profile": RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE.immutable_configuration,
            "pipeline_code": PIPELINE_CODE,
            "pipeline_version": PIPELINE_VERSION,
            "stage_code": STAGE_CODE,
            "stage_version": STAGE_VERSION,
        }
        encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return f"sha256:{sha256(encoded).hexdigest()}"

    def provider_adoption_profile(
        self,
        allowed_origins: tuple[str, ...],
    ) -> ProviderAdoptionProfile:
        return ProviderAdoptionProfile(
            adapter_code=self.adapter_code,
            allowed_origins=allowed_origins,
            allowed_methods=(ProviderHttpMethod.GET,),
            allowed_media_types=RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE.accepted_media_types,
            connect_timeout_ms=self.connect_timeout_ms,
            read_timeout_ms=self.read_timeout_ms,
            total_timeout_ms=self.total_timeout_ms,
            max_response_bytes=RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE.max_document_bytes,
            max_redirect_hops=self.max_redirect_hops,
            terms_evidence_ref=self.terms_evidence_ref,
            rate_limit_evidence_ref=self.rate_limit_evidence_ref,
        )


class RssAtomSubscriptionManifestRegistry:
    def __init__(
        self,
        manifests: tuple[RssAtomSubscriptionManifest, ...] = (),
    ) -> None:
        subscriptions: dict[str, RssAtomSubscriptionManifest] = {}
        adapters: dict[str, list[RssAtomSubscriptionManifest]] = {}
        locators: set[tuple[str, str]] = set()
        for manifest in manifests:
            if type(manifest) is not RssAtomSubscriptionManifest:
                raise ValueError("subscription registry requires exact manifests")
            if manifest.subscription_code in subscriptions:
                raise ValueError("duplicate RSS/Atom subscription code")
            locator_key = (manifest.adapter_code, manifest.external_locator)
            if locator_key in locators:
                raise ValueError("duplicate RSS/Atom adapter locator")
            existing_group = adapters.get(manifest.adapter_code)
            if existing_group and existing_group[0].adapter_policy != manifest.adapter_policy:
                raise ValueError("shared RSS/Atom adapter policy drift")
            subscriptions[manifest.subscription_code] = manifest
            adapters.setdefault(manifest.adapter_code, []).append(manifest)
            locators.add(locator_key)

        self._subscriptions = MappingProxyType(
            {code: subscriptions[code] for code in sorted(subscriptions)}
        )
        self._adapters = MappingProxyType(
            {
                code: tuple(
                    sorted(adapters[code], key=lambda item: item.subscription_code)
                )
                for code in sorted(adapters)
            }
        )

    def get(self, subscription_code: str) -> RssAtomSubscriptionManifest:
        require_versioned_adapter_code(subscription_code)
        try:
            return self._subscriptions[subscription_code]
        except KeyError as exc:
            raise KeyError(subscription_code) from exc

    @property
    def manifests(self) -> tuple[RssAtomSubscriptionManifest, ...]:
        return tuple(self._subscriptions.values())

    @property
    def adapter_codes(self) -> tuple[str, ...]:
        return tuple(self._adapters)

    def for_adapter(
        self,
        adapter_code: str,
    ) -> tuple[RssAtomSubscriptionManifest, ...]:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._adapters[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc

    def __len__(self) -> int:
        return len(self._subscriptions)


def build_rss_atom_provider_adoption_registry(
    registry: RssAtomSubscriptionManifestRegistry,
) -> ProviderAdoptionRegistry:
    profiles: list[ProviderAdoptionProfile] = []
    for adapter_code in registry.adapter_codes:
        manifests = registry.for_adapter(adapter_code)
        first = manifests[0]
        origins = tuple(sorted({manifest.origin for manifest in manifests}))
        profiles.append(first.provider_adoption_profile(origins))
    return InMemoryProviderAdoptionRegistry(tuple(profiles))


def build_rss_atom_public_capture_registry(
    *,
    registry: RssAtomSubscriptionManifestRegistry,
    factory: EvidenceBackedPublicHttpCaptureAdapterFactory,
) -> PublicSourceCaptureRegistry:
    adapters = tuple(
        factory.create(
            StrictRssAtomCaptureDefinition(
                adapter_code=adapter_code,
                profile=RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE,
            )
        )
        for adapter_code in registry.adapter_codes
    )
    return InMemoryPublicSourceCaptureRegistry(adapters)


def build_rss_atom_ingestion_worker_registry(
    *,
    registry: RssAtomSubscriptionManifestRegistry,
    knowledge: KnowledgeRepository,
    evidence: RawSourceEvidenceReader,
) -> IngestionWorkerRuntimeRegistry:
    if len(registry) == 0:
        return InMemoryIngestionWorkerRuntimeRegistry()
    processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
        profile=RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE,
    )
    return build_feed_item_extraction_runtime(processor)


@dataclass(frozen=True, slots=True)
class RssAtomSubscriptionActivationResult:
    subscription_code: str
    adapter_code: str
    provider_capability: SourceProviderCapability
    schedule: SourceAcquisitionSchedule

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.subscription_code)
        require_versioned_adapter_code(self.adapter_code)
        if self.provider_capability.adapter_code != self.adapter_code:
            raise ValueError("activation capability adapter mismatch")
        if self.schedule.adapter_code != self.adapter_code:
            raise ValueError("activation schedule adapter mismatch")


class RssAtomSubscriptionActivationService:
    def __init__(
        self,
        *,
        registry: RssAtomSubscriptionManifestRegistry,
        admission: SourceProviderAdmissionService,
        scheduler: SourceAcquisitionSchedulerService,
    ) -> None:
        self._registry = registry
        self._admission = admission
        self._scheduler = scheduler

    def activate(
        self,
        *,
        subscription_code: str,
        first_due_at: datetime,
        activated_at: datetime,
    ) -> RssAtomSubscriptionActivationResult:
        _require_utc(first_due_at, "first_due_at")
        _require_utc(activated_at, "activated_at")
        manifest = self._registry.get(subscription_code)

        capability = self._admission.register(
            adapter_code=manifest.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=manifest.quota_limit,
            quota_window_seconds=manifest.quota_window_seconds,
            failure_threshold=manifest.failure_threshold,
            circuit_open_seconds=manifest.circuit_open_seconds,
            permit_ttl_seconds=manifest.permit_ttl_seconds,
            created_at=activated_at,
        )
        schedule = self._scheduler.create_schedule(
            adapter_code=manifest.adapter_code,
            external_locator=manifest.external_locator,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=manifest.configuration_hash,
            first_due_at=first_due_at,
            interval_seconds=manifest.interval_seconds,
            max_dispatch_attempts=manifest.max_dispatch_attempts,
            locale=manifest.locale,
            jurisdiction_code=manifest.jurisdiction_code,
            now=activated_at,
        )
        return RssAtomSubscriptionActivationResult(
            subscription_code=manifest.subscription_code,
            adapter_code=manifest.adapter_code,
            provider_capability=capability,
            schedule=schedule,
        )


__all__ = [
    "RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE",
    "RssAtomSubscriptionActivationResult",
    "RssAtomSubscriptionActivationService",
    "RssAtomSubscriptionManifest",
    "RssAtomSubscriptionManifestRegistry",
    "build_rss_atom_ingestion_worker_registry",
    "build_rss_atom_provider_adoption_registry",
    "build_rss_atom_public_capture_registry",
]

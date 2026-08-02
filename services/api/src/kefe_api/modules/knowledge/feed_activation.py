from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from threading import Lock
from types import MappingProxyType
from typing import Protocol
from urllib.parse import urlsplit

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE as EXTRACTION_PIPELINE_CODE,
    PIPELINE_VERSION as EXTRACTION_PIPELINE_VERSION,
    STAGE_CODE as EXTRACTION_STAGE_CODE,
    STAGE_VERSION as EXTRACTION_STAGE_VERSION,
)
from kefe_api.modules.ingestion_orchestration.models import ExecutorKind
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCapabilityLifecycle,
    ProviderCredentialMode,
)
from kefe_api.modules.knowledge.provider_control_ports import (
    SourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_http_auth import ProviderHttpAuthRegistry
from kefe_api.modules.knowledge.provider_http_transport import (
    ProviderAdoptionProfile,
    ProviderAdoptionRegistry,
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

_SHA256_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_EVIDENCE_REF = re.compile(r"^evidence://capability/[A-Za-z0-9._/@:+-]+$")
_REASON_CODE = re.compile(r"^FEED_ACTIVATION_[A-Z0-9_]{1,80}$")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _require_hash(value: str, field_name: str) -> None:
    if _SHA256_HASH.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be canonical SHA-256")


def _canonical_https_locator(value: str) -> str:
    if not value or value != value.strip() or len(value) > 4096:
        raise ValueError("external_locator must be bounded exact text")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("external_locator is invalid") from exc
    if parsed.scheme != "https" or parsed.hostname is None:
        raise ValueError("external_locator must be absolute HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("external_locator cannot contain userinfo")
    if parsed.fragment or port not in (None, 443):
        raise ValueError("external_locator fragment or port is invalid")
    try:
        parsed.hostname.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("external_locator hostname must be ASCII") from exc
    return value


def _hash_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{sha256(encoded).hexdigest()}"


def adoption_configuration_hash(profile: ProviderAdoptionProfile) -> str:
    return _hash_payload(
        {
            "adapter_code": profile.adapter_code,
            "allowed_origins": list(profile.allowed_origins),
            "allowed_methods": sorted(method.value for method in profile.allowed_methods),
            "allowed_media_types": list(profile.allowed_media_types),
            "connect_timeout_ms": profile.connect_timeout_ms,
            "read_timeout_ms": profile.read_timeout_ms,
            "total_timeout_ms": profile.total_timeout_ms,
            "max_response_bytes": profile.max_response_bytes,
            "max_redirect_hops": profile.max_redirect_hops,
            "terms_evidence_ref": profile.terms_evidence_ref,
            "rate_limit_evidence_ref": profile.rate_limit_evidence_ref,
        }
    )


def parser_configuration_hash(profile: StrictRssAtomParseProfile) -> str:
    return _hash_payload(
        {
            "accepted_media_types": list(profile.accepted_media_types),
            "max_document_bytes": profile.max_document_bytes,
            "max_elements": profile.max_elements,
            "max_depth": profile.max_depth,
            "max_items": profile.max_items,
            "max_node_text_chars": profile.max_node_text_chars,
            "max_total_text_chars": profile.max_total_text_chars,
            "max_attributes_per_element": profile.max_attributes_per_element,
            "max_total_attribute_chars": profile.max_total_attribute_chars,
            "max_metadata_field_chars": profile.max_metadata_field_chars,
        }
    )


class FeedPipelineLifecycle(StrEnum):
    DRAFT = "DRAFT"
    PAUSED = "PAUSED"
    ENABLED = "ENABLED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True, repr=False)
class FeedPipelineDefinition:
    feed_code: str
    adapter_code: str
    external_locator: str
    adoption_configuration_hash: str
    parser_configuration_hash: str
    extraction_pipeline_code: str
    extraction_pipeline_version: str
    acquisition_configuration_hash: str
    interval_seconds: int
    max_dispatch_attempts: int
    evidence_capability_ref: str
    lifecycle_state: FeedPipelineLifecycle
    dependency_fingerprint: str | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.feed_code)
        require_versioned_adapter_code(self.adapter_code)
        if self.external_locator != _canonical_https_locator(self.external_locator):
            raise ValueError("external_locator must be canonical")
        _require_hash(self.adoption_configuration_hash, "adoption_configuration_hash")
        _require_hash(self.parser_configuration_hash, "parser_configuration_hash")
        _require_hash(
            self.acquisition_configuration_hash,
            "acquisition_configuration_hash",
        )
        if not self.extraction_pipeline_code.strip():
            raise ValueError("extraction_pipeline_code must not be blank")
        if not self.extraction_pipeline_version.strip():
            raise ValueError("extraction_pipeline_version must not be blank")
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the scheduler bounds")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the scheduler bounds")
        if _EVIDENCE_REF.fullmatch(self.evidence_capability_ref) is None:
            raise ValueError("evidence_capability_ref is invalid")
        if type(self.lifecycle_state) is not FeedPipelineLifecycle:
            raise ValueError("lifecycle_state must be exact FeedPipelineLifecycle")
        if self.dependency_fingerprint is not None:
            _require_hash(self.dependency_fingerprint, "dependency_fingerprint")
        if (self.dependency_fingerprint is None) != (self.verified_at is None):
            raise ValueError("dependency fingerprint and verified_at must coexist")
        for value, field_name in (
            (self.created_at, "created_at"),
            (self.updated_at, "updated_at"),
        ):
            _require_utc(value, field_name)
        if self.verified_at is not None:
            _require_utc(self.verified_at, "verified_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")

    @classmethod
    def create(
        cls,
        *,
        feed_code: str,
        adapter_code: str,
        external_locator: str,
        adoption_configuration_hash: str,
        parser_configuration_hash: str,
        extraction_pipeline_code: str,
        extraction_pipeline_version: str,
        acquisition_configuration_hash: str,
        interval_seconds: int,
        max_dispatch_attempts: int,
        evidence_capability_ref: str,
        created_at: datetime,
    ) -> FeedPipelineDefinition:
        return cls(
            feed_code=feed_code,
            adapter_code=adapter_code,
            external_locator=external_locator,
            adoption_configuration_hash=adoption_configuration_hash,
            parser_configuration_hash=parser_configuration_hash,
            extraction_pipeline_code=extraction_pipeline_code,
            extraction_pipeline_version=extraction_pipeline_version,
            acquisition_configuration_hash=acquisition_configuration_hash,
            interval_seconds=interval_seconds,
            max_dispatch_attempts=max_dispatch_attempts,
            evidence_capability_ref=evidence_capability_ref,
            lifecycle_state=FeedPipelineLifecycle.DRAFT,
            dependency_fingerprint=None,
            verified_at=None,
            created_at=created_at,
            updated_at=created_at,
        )

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.feed_code,
            self.adapter_code,
            self.external_locator,
            self.adoption_configuration_hash,
            self.parser_configuration_hash,
            self.extraction_pipeline_code,
            self.extraction_pipeline_version,
            self.acquisition_configuration_hash,
            self.interval_seconds,
            self.max_dispatch_attempts,
            self.evidence_capability_ref,
        )

    def transition(
        self,
        target: FeedPipelineLifecycle,
        *,
        at: datetime,
        dependency_fingerprint: str | None = None,
    ) -> FeedPipelineDefinition:
        _require_utc(at, "at")
        allowed = {
            FeedPipelineLifecycle.DRAFT: {
                FeedPipelineLifecycle.ENABLED,
                FeedPipelineLifecycle.RETIRED,
            },
            FeedPipelineLifecycle.ENABLED: {
                FeedPipelineLifecycle.PAUSED,
                FeedPipelineLifecycle.RETIRED,
            },
            FeedPipelineLifecycle.PAUSED: {
                FeedPipelineLifecycle.ENABLED,
                FeedPipelineLifecycle.RETIRED,
            },
            FeedPipelineLifecycle.RETIRED: set(),
        }
        if target not in allowed[self.lifecycle_state]:
            raise ValueError("feed pipeline lifecycle transition is invalid")
        verified_at = self.verified_at
        fingerprint = self.dependency_fingerprint
        if target is FeedPipelineLifecycle.ENABLED:
            if dependency_fingerprint is None:
                raise ValueError("enabling requires a dependency fingerprint")
            _require_hash(dependency_fingerprint, "dependency_fingerprint")
            fingerprint = dependency_fingerprint
            verified_at = at
        return replace(
            self,
            lifecycle_state=target,
            dependency_fingerprint=fingerprint,
            verified_at=verified_at,
            updated_at=at,
        )

    def __repr__(self) -> str:
        return (
            "FeedPipelineDefinition("
            f"feed_code={self.feed_code!r}, adapter_code={self.adapter_code!r}, "
            "external_locator=<redacted>, adoption_configuration_hash=<redacted>, "
            "parser_configuration_hash=<redacted>, "
            f"extraction_pipeline_code={self.extraction_pipeline_code!r}, "
            f"extraction_pipeline_version={self.extraction_pipeline_version!r}, "
            "acquisition_configuration_hash=<redacted>, "
            f"interval_seconds={self.interval_seconds}, "
            f"max_dispatch_attempts={self.max_dispatch_attempts}, "
            "evidence_capability_ref=<redacted>, "
            f"lifecycle_state={self.lifecycle_state.value!r}, "
            "dependency_fingerprint=<redacted>, "
            f"verified_at={self.verified_at!r})"
        )


class FeedPipelineDefinitionRepository(Protocol):
    def create_or_get(
        self,
        definition: FeedPipelineDefinition,
    ) -> FeedPipelineDefinition: ...

    def get(self, feed_code: str) -> FeedPipelineDefinition | None: ...

    def transition(
        self,
        *,
        feed_code: str,
        target: FeedPipelineLifecycle,
        at: datetime,
        dependency_fingerprint: str | None = None,
    ) -> FeedPipelineDefinition: ...


class InMemoryFeedPipelineDefinitionRepository:
    def __init__(self) -> None:
        self._definitions: dict[str, FeedPipelineDefinition] = {}
        self._lock = Lock()

    def create_or_get(
        self,
        definition: FeedPipelineDefinition,
    ) -> FeedPipelineDefinition:
        with self._lock:
            existing = self._definitions.get(definition.feed_code)
            if existing is None:
                self._definitions[definition.feed_code] = definition
                return definition
            if existing.immutable_configuration != definition.immutable_configuration:
                raise ValueError("feed pipeline configuration is immutable")
            return existing

    def get(self, feed_code: str) -> FeedPipelineDefinition | None:
        require_versioned_adapter_code(feed_code)
        with self._lock:
            return self._definitions.get(feed_code)

    def transition(
        self,
        *,
        feed_code: str,
        target: FeedPipelineLifecycle,
        at: datetime,
        dependency_fingerprint: str | None = None,
    ) -> FeedPipelineDefinition:
        with self._lock:
            try:
                current = self._definitions[feed_code]
            except KeyError as exc:
                raise KeyError(feed_code) from exc
            updated = current.transition(
                target,
                at=at,
                dependency_fingerprint=dependency_fingerprint,
            )
            self._definitions[feed_code] = updated
            return updated

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._definitions)


class FeedParserProfileRegistry(Protocol):
    def get(self, configuration_hash: str) -> StrictRssAtomParseProfile: ...


class InMemoryFeedParserProfileRegistry:
    def __init__(self, profiles: tuple[StrictRssAtomParseProfile, ...] = ()) -> None:
        entries: dict[str, StrictRssAtomParseProfile] = {}
        for profile in profiles:
            configuration_hash = parser_configuration_hash(profile)
            if configuration_hash in entries:
                raise ValueError("duplicate feed parser profile")
            entries[configuration_hash] = profile
        self._profiles = MappingProxyType(entries)

    def get(self, configuration_hash: str) -> StrictRssAtomParseProfile:
        _require_hash(configuration_hash, "configuration_hash")
        try:
            return self._profiles[configuration_hash]
        except KeyError as exc:
            raise KeyError(configuration_hash) from exc


class FeedActivationOutcome(StrEnum):
    VERIFIED = "VERIFIED"
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class FeedActivationResult:
    outcome: FeedActivationOutcome
    feed_code: str
    lifecycle_state: FeedPipelineLifecycle
    reason_code: str
    dependency_fingerprint: str | None
    verified_at: datetime | None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.feed_code)
        if _REASON_CODE.fullmatch(self.reason_code) is None:
            raise ValueError("reason_code is invalid")
        if self.dependency_fingerprint is not None:
            _require_hash(self.dependency_fingerprint, "dependency_fingerprint")
        if self.verified_at is not None:
            _require_utc(self.verified_at, "verified_at")

    def as_operational_dict(self) -> dict[str, str | None]:
        return {
            "outcome": self.outcome.value,
            "feed_code": self.feed_code,
            "lifecycle_state": self.lifecycle_state.value,
            "reason_code": self.reason_code,
            "dependency_fingerprint": self.dependency_fingerprint,
            "verified_at": (
                self.verified_at.isoformat() if self.verified_at is not None else None
            ),
        }


class FeedActivationService:
    def __init__(
        self,
        *,
        definitions: FeedPipelineDefinitionRepository,
        providers: SourceProviderAdmissionRepository,
        adoption_profiles: ProviderAdoptionRegistry,
        auth_profiles: ProviderHttpAuthRegistry,
        evidence_store: RawSourceEvidenceStore,
        parser_profiles: FeedParserProfileRegistry,
        public_http_factory: EvidenceBackedPublicHttpCaptureAdapterFactory,
        ingestion_runtime: IngestionWorkerRuntimeRegistry,
    ) -> None:
        self._definitions = definitions
        self._providers = providers
        self._adoption_profiles = adoption_profiles
        self._auth_profiles = auth_profiles
        self._evidence_store = evidence_store
        self._parser_profiles = parser_profiles
        self._public_http_factory = public_http_factory
        self._ingestion_runtime = ingestion_runtime

    def register(self, definition: FeedPipelineDefinition) -> FeedPipelineDefinition:
        return self._definitions.create_or_get(definition)

    def preflight(
        self,
        feed_code: str,
        *,
        at: datetime,
    ) -> FeedActivationResult:
        definition = self._definitions.get(feed_code)
        if definition is None:
            return self._missing(feed_code)
        blocked = self._verify_dependencies(definition, at=at)
        if isinstance(blocked, FeedActivationResult):
            return blocked
        return FeedActivationResult(
            outcome=FeedActivationOutcome.VERIFIED,
            feed_code=definition.feed_code,
            lifecycle_state=definition.lifecycle_state,
            reason_code="FEED_ACTIVATION_PREFLIGHT_VERIFIED",
            dependency_fingerprint=blocked,
            verified_at=at,
        )

    def enable(self, feed_code: str, *, at: datetime) -> FeedActivationResult:
        return self._enable_or_resume(feed_code, at=at)

    def resume(self, feed_code: str, *, at: datetime) -> FeedActivationResult:
        return self._enable_or_resume(feed_code, at=at)

    def pause(self, feed_code: str, *, at: datetime) -> FeedActivationResult:
        return self._transition_without_preflight(
            feed_code,
            target=FeedPipelineLifecycle.PAUSED,
            outcome=FeedActivationOutcome.PAUSED,
            reason_code="FEED_ACTIVATION_PAUSED",
            at=at,
        )

    def retire(self, feed_code: str, *, at: datetime) -> FeedActivationResult:
        return self._transition_without_preflight(
            feed_code,
            target=FeedPipelineLifecycle.RETIRED,
            outcome=FeedActivationOutcome.RETIRED,
            reason_code="FEED_ACTIVATION_RETIRED",
            at=at,
        )

    def _enable_or_resume(
        self,
        feed_code: str,
        *,
        at: datetime,
    ) -> FeedActivationResult:
        preflight = self.preflight(feed_code, at=at)
        if preflight.outcome is FeedActivationOutcome.BLOCKED:
            return preflight
        try:
            updated = self._definitions.transition(
                feed_code=feed_code,
                target=FeedPipelineLifecycle.ENABLED,
                at=at,
                dependency_fingerprint=preflight.dependency_fingerprint,
            )
        except (KeyError, ValueError):
            current = self._definitions.get(feed_code)
            if current is None:
                return self._missing(feed_code)
            return self._blocked(current, "FEED_ACTIVATION_LIFECYCLE_INVALID")
        return FeedActivationResult(
            outcome=FeedActivationOutcome.ENABLED,
            feed_code=updated.feed_code,
            lifecycle_state=updated.lifecycle_state,
            reason_code="FEED_ACTIVATION_ENABLED",
            dependency_fingerprint=updated.dependency_fingerprint,
            verified_at=updated.verified_at,
        )

    def _transition_without_preflight(
        self,
        feed_code: str,
        *,
        target: FeedPipelineLifecycle,
        outcome: FeedActivationOutcome,
        reason_code: str,
        at: datetime,
    ) -> FeedActivationResult:
        try:
            updated = self._definitions.transition(
                feed_code=feed_code,
                target=target,
                at=at,
            )
        except KeyError:
            return self._missing(feed_code)
        except ValueError:
            current = self._definitions.get(feed_code)
            if current is None:
                return self._missing(feed_code)
            return self._blocked(current, "FEED_ACTIVATION_LIFECYCLE_INVALID")
        return FeedActivationResult(
            outcome=outcome,
            feed_code=updated.feed_code,
            lifecycle_state=updated.lifecycle_state,
            reason_code=reason_code,
            dependency_fingerprint=updated.dependency_fingerprint,
            verified_at=updated.verified_at,
        )

    def _verify_dependencies(
        self,
        definition: FeedPipelineDefinition,
        *,
        at: datetime,
    ) -> str | FeedActivationResult:
        _require_utc(at, "at")
        capability = self._providers.get(definition.adapter_code)
        if capability is None:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_PROVIDER_NOT_REGISTERED",
            )
        if capability.credential_mode is not ProviderCredentialMode.PUBLIC:
            return self._blocked(definition, "FEED_ACTIVATION_PROVIDER_NOT_PUBLIC")
        if capability.lifecycle_state is not ProviderCapabilityLifecycle.ENABLED:
            return self._blocked(definition, "FEED_ACTIVATION_PROVIDER_NOT_ENABLED")

        try:
            adoption = self._adoption_profiles.get(definition.adapter_code)
        except KeyError:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_ADOPTION_PROFILE_NOT_REGISTERED",
            )
        actual_adoption_hash = adoption_configuration_hash(adoption)
        if actual_adoption_hash != definition.adoption_configuration_hash:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_ADOPTION_PROFILE_MISMATCH",
            )

        try:
            self._auth_profiles.get(definition.adapter_code)
        except KeyError:
            pass
        else:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_AUTH_PROFILE_FORBIDDEN",
            )

        if getattr(self._evidence_store, "configured", False) is not True:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_EVIDENCE_UNAVAILABLE",
            )
        if getattr(self._evidence_store, "capability_ref", None) != (
            definition.evidence_capability_ref
        ):
            return self._blocked(
                definition,
                "FEED_ACTIVATION_EVIDENCE_CAPABILITY_MISMATCH",
            )

        try:
            parser_profile = self._parser_profiles.get(
                definition.parser_configuration_hash
            )
        except KeyError:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_PUBLIC_ADAPTER_INVALID",
            )
        if parser_configuration_hash(parser_profile) != (
            definition.parser_configuration_hash
        ):
            return self._blocked(
                definition,
                "FEED_ACTIVATION_PUBLIC_ADAPTER_INVALID",
            )
        try:
            adapter = self._public_http_factory.create(
                StrictRssAtomCaptureDefinition(
                    adapter_code=definition.adapter_code,
                    profile=parser_profile,
                )
            )
        except Exception:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_PUBLIC_ADAPTER_INVALID",
            )
        if adapter.adapter_code != definition.adapter_code:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_PUBLIC_ADAPTER_INVALID",
            )

        try:
            runtime_plan = self._ingestion_runtime.get_plan(
                pipeline_code=definition.extraction_pipeline_code,
                pipeline_version=definition.extraction_pipeline_version,
            )
        except KeyError:
            return self._blocked(
                definition,
                "FEED_ACTIVATION_RUNTIME_PLAN_NOT_REGISTERED",
            )
        if (
            definition.extraction_pipeline_code != EXTRACTION_PIPELINE_CODE
            or definition.extraction_pipeline_version != EXTRACTION_PIPELINE_VERSION
            or len(runtime_plan.stages) != 1
            or runtime_plan.stages[0].stage_code != EXTRACTION_STAGE_CODE
            or runtime_plan.stages[0].stage_version != EXTRACTION_STAGE_VERSION
            or runtime_plan.stages[0].executor_kind is not ExecutorKind.DETERMINISTIC
        ):
            return self._blocked(
                definition,
                "FEED_ACTIVATION_RUNTIME_PLAN_MISMATCH",
            )

        if not (
            MINIMUM_INTERVAL_SECONDS
            <= definition.interval_seconds
            <= MAXIMUM_INTERVAL_SECONDS
        ) or not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= definition.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            return self._blocked(
                definition,
                "FEED_ACTIVATION_SCHEDULE_INVALID",
            )

        fingerprint = _hash_payload(
            {
                "feed_code": definition.feed_code,
                "adapter_code": definition.adapter_code,
                "external_locator": definition.external_locator,
                "adoption_configuration_hash": actual_adoption_hash,
                "parser_configuration_hash": parser_configuration_hash(parser_profile),
                "extraction_pipeline_code": runtime_plan.pipeline_code,
                "extraction_pipeline_version": runtime_plan.pipeline_version,
                "extraction_stages": [
                    {
                        "stage_code": stage.stage_code,
                        "stage_version": stage.stage_version,
                        "max_attempts": stage.max_attempts,
                        "executor_kind": stage.executor_kind.value,
                    }
                    for stage in runtime_plan.stages
                ],
                "acquisition_configuration_hash": (
                    definition.acquisition_configuration_hash
                ),
                "interval_seconds": definition.interval_seconds,
                "max_dispatch_attempts": definition.max_dispatch_attempts,
                "evidence_capability_ref": definition.evidence_capability_ref,
            }
        )
        if (
            definition.dependency_fingerprint is not None
            and definition.dependency_fingerprint != fingerprint
        ):
            return self._blocked(
                definition,
                "FEED_ACTIVATION_DEPENDENCY_DRIFT",
            )
        return fingerprint

    @staticmethod
    def _missing(feed_code: str) -> FeedActivationResult:
        require_versioned_adapter_code(feed_code)
        return FeedActivationResult(
            outcome=FeedActivationOutcome.BLOCKED,
            feed_code=feed_code,
            lifecycle_state=FeedPipelineLifecycle.DRAFT,
            reason_code="FEED_ACTIVATION_DEFINITION_NOT_FOUND",
            dependency_fingerprint=None,
            verified_at=None,
        )

    @staticmethod
    def _blocked(
        definition: FeedPipelineDefinition,
        reason_code: str,
    ) -> FeedActivationResult:
        return FeedActivationResult(
            outcome=FeedActivationOutcome.BLOCKED,
            feed_code=definition.feed_code,
            lifecycle_state=definition.lifecycle_state,
            reason_code=reason_code,
            dependency_fingerprint=definition.dependency_fingerprint,
            verified_at=definition.verified_at,
        )


__all__ = [
    "FeedActivationOutcome",
    "FeedActivationResult",
    "FeedActivationService",
    "FeedParserProfileRegistry",
    "FeedPipelineDefinition",
    "FeedPipelineDefinitionRepository",
    "FeedPipelineLifecycle",
    "InMemoryFeedParserProfileRegistry",
    "InMemoryFeedPipelineDefinitionRepository",
    "adoption_configuration_hash",
    "parser_configuration_hash",
]

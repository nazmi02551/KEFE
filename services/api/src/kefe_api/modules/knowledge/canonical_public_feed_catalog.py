from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from threading import RLock
from typing import Protocol
from uuid import UUID, uuid5

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_capture import (
    ProviderHttpCaptureDefinition,
)
from kefe_api.modules.knowledge.provider_http_transport import ProviderAdoptionProfile
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomCaptureDefinition,
)
from kefe_api.modules.knowledge.source_acquisition import SourceAcquisitionCommand
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceAcquisitionSchedulerService,
)

_CATALOG_NAMESPACE = UUID("7f44ed40-486e-4dbe-b21d-a9a6f55ee4a5")
_ACTIVATION_NAMESPACE = UUID("144ea98d-40b5-49a7-a596-c9bb12487d23")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must be timezone-aware UTC")


def _require_actor(value: str, field: str) -> None:
    if not value.strip() or len(value) > 160:
        raise ValueError(f"{field} must be bounded non-blank text")


def _hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


class PublicFeedCatalogState(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    RETIRED = "RETIRED"


class PublicFeedActivationState(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class PublicFeedAuditAction(StrEnum):
    DRAFT_REGISTERED = "DRAFT_REGISTERED"
    PREFLIGHT_SUCCEEDED = "PREFLIGHT_SUCCEEDED"
    APPROVED = "APPROVED"
    ACTIVATED = "ACTIVATED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    ACTIVATION_RETIRED = "ACTIVATION_RETIRED"
    DEFINITION_RETIRED = "DEFINITION_RETIRED"


@dataclass(frozen=True, slots=True)
class CanonicalPublicFeedDefinition:
    id: UUID
    feed_code: str
    definition_version: int
    definition: PublicFeedDefinition
    interval_seconds: int
    max_dispatch_attempts: int
    configuration_hash: str
    state: PublicFeedCatalogState
    created_at: datetime
    created_by_actor_ref: str
    preflighted_at: datetime | None = None
    preflighted_by_actor_ref: str | None = None
    approved_at: datetime | None = None
    approved_by_actor_ref: str | None = None
    retired_at: datetime | None = None
    retired_by_actor_ref: str | None = None

    def __post_init__(self) -> None:
        if self.feed_code != self.definition.feed_code:
            raise ValueError("feed_code must match the embedded definition")
        if self.definition_version < 1:
            raise ValueError("definition_version must be positive")
        if not self.definition.adapter_code.endswith(f".v{self.definition_version}"):
            raise ValueError("adapter_code version must match definition_version")
        if self.interval_seconds < 60 or self.interval_seconds > 31_536_000:
            raise ValueError("interval_seconds is outside the supported range")
        if self.max_dispatch_attempts < 1 or self.max_dispatch_attempts > 20:
            raise ValueError("max_dispatch_attempts is outside the supported range")
        if self.configuration_hash != self.compute_configuration_hash(
            definition=self.definition,
            definition_version=self.definition_version,
            interval_seconds=self.interval_seconds,
            max_dispatch_attempts=self.max_dispatch_attempts,
        ):
            raise ValueError("configuration_hash does not match immutable definition")
        _require_utc(self.created_at, "created_at")
        _require_actor(self.created_by_actor_ref, "created_by_actor_ref")
        for value, field in (
            (self.preflighted_at, "preflighted_at"),
            (self.approved_at, "approved_at"),
            (self.retired_at, "retired_at"),
        ):
            if value is not None:
                _require_utc(value, field)
        for value, field in (
            (self.preflighted_by_actor_ref, "preflighted_by_actor_ref"),
            (self.approved_by_actor_ref, "approved_by_actor_ref"),
            (self.retired_by_actor_ref, "retired_by_actor_ref"),
        ):
            if value is not None:
                _require_actor(value, field)
        if self.state is PublicFeedCatalogState.DRAFT:
            if self.approved_at is not None or self.approved_by_actor_ref is not None:
                raise ValueError("DRAFT definition cannot be approved")
            if self.retired_at is not None or self.retired_by_actor_ref is not None:
                raise ValueError("DRAFT definition cannot contain retirement")
        elif self.state is PublicFeedCatalogState.APPROVED:
            if self.preflighted_at is None or self.preflighted_by_actor_ref is None:
                raise ValueError("APPROVED definition requires successful preflight")
            if self.approved_at is None or self.approved_by_actor_ref is None:
                raise ValueError("APPROVED definition requires approval metadata")
            if self.retired_at is not None or self.retired_by_actor_ref is not None:
                raise ValueError("APPROVED definition cannot contain retirement")
        else:
            if self.retired_at is None or self.retired_by_actor_ref is None:
                raise ValueError("RETIRED definition requires retirement metadata")

    @classmethod
    def create(
        cls,
        *,
        definition_version: int,
        definition: PublicFeedDefinition,
        interval_seconds: int,
        max_dispatch_attempts: int,
        created_at: datetime,
        created_by_actor_ref: str,
    ) -> CanonicalPublicFeedDefinition:
        configuration_hash = cls.compute_configuration_hash(
            definition=definition,
            definition_version=definition_version,
            interval_seconds=interval_seconds,
            max_dispatch_attempts=max_dispatch_attempts,
        )
        return cls(
            id=uuid5(
                _CATALOG_NAMESPACE,
                f"{definition.feed_code}:{definition_version}:{configuration_hash}",
            ),
            feed_code=definition.feed_code,
            definition_version=definition_version,
            definition=definition,
            interval_seconds=interval_seconds,
            max_dispatch_attempts=max_dispatch_attempts,
            configuration_hash=configuration_hash,
            state=PublicFeedCatalogState.DRAFT,
            created_at=created_at,
            created_by_actor_ref=created_by_actor_ref,
        )

    @staticmethod
    def compute_configuration_hash(
        *,
        definition: PublicFeedDefinition,
        definition_version: int,
        interval_seconds: int,
        max_dispatch_attempts: int,
    ) -> str:
        return _hash(
            {
                "feed_code": definition.feed_code,
                "definition_version": definition_version,
                "display_name": definition.display_name,
                "adapter_code": definition.adapter_code,
                "external_locator": definition.external_locator,
                "parser_profile": definition.parser_profile.immutable_configuration,
                "connect_timeout_ms": definition.connect_timeout_ms,
                "read_timeout_ms": definition.read_timeout_ms,
                "total_timeout_ms": definition.total_timeout_ms,
                "max_response_bytes": definition.max_response_bytes,
                "max_redirect_hops": definition.max_redirect_hops,
                "terms_evidence_ref": definition.terms_evidence_ref,
                "rate_limit_evidence_ref": definition.rate_limit_evidence_ref,
                "quota_limit": definition.quota_limit,
                "quota_window_seconds": definition.quota_window_seconds,
                "failure_threshold": definition.failure_threshold,
                "circuit_open_seconds": definition.circuit_open_seconds,
                "permit_ttl_seconds": definition.permit_ttl_seconds,
                "interval_seconds": interval_seconds,
                "max_dispatch_attempts": max_dispatch_attempts,
                "language_code": definition.language_code,
                "jurisdiction_code": definition.jurisdiction_code,
                "pipeline_code": PIPELINE_CODE,
                "pipeline_version": PIPELINE_VERSION,
                "ingestion_configuration_hash": definition.configuration_hash,
            }
        )

    def mark_preflight(self, *, actor_ref: str, at: datetime) -> CanonicalPublicFeedDefinition:
        if self.state is not PublicFeedCatalogState.DRAFT:
            raise ValueError("only DRAFT definition may be preflighted")
        return replace(
            self,
            preflighted_at=at,
            preflighted_by_actor_ref=actor_ref,
        )

    def approve(self, *, actor_ref: str, at: datetime) -> CanonicalPublicFeedDefinition:
        if self.state is not PublicFeedCatalogState.DRAFT:
            raise ValueError("only DRAFT definition may be approved")
        if self.preflighted_at is None:
            raise ValueError("definition must pass preflight before approval")
        if actor_ref == self.created_by_actor_ref:
            raise ValueError("definition creator cannot approve the same version")
        return replace(
            self,
            state=PublicFeedCatalogState.APPROVED,
            approved_at=at,
            approved_by_actor_ref=actor_ref,
        )

    def retire(self, *, actor_ref: str, at: datetime) -> CanonicalPublicFeedDefinition:
        if self.state is PublicFeedCatalogState.RETIRED:
            raise ValueError("definition is already RETIRED")
        return replace(
            self,
            state=PublicFeedCatalogState.RETIRED,
            retired_at=at,
            retired_by_actor_ref=actor_ref,
        )


@dataclass(frozen=True, slots=True)
class PublicFeedPreflightResult:
    feed_definition_id: UUID
    configuration_hash: str
    adapter_code: str
    external_locator: str
    allowed_origin: str
    pipeline_code: str
    pipeline_version: str
    interval_seconds: int
    max_dispatch_attempts: int


@dataclass(frozen=True, slots=True)
class PublicFeedRuntimeProfile:
    feed_definition_id: UUID
    configuration_hash: str
    adoption_profile: ProviderAdoptionProfile
    capture_definition: ProviderHttpCaptureDefinition
    acquisition_command: SourceAcquisitionCommand


class PublicFeedRuntimeProfileRegistry(Protocol):
    def register_or_get(self, profile: PublicFeedRuntimeProfile) -> PublicFeedRuntimeProfile: ...


class InMemoryPublicFeedRuntimeProfileRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._by_adapter: dict[str, PublicFeedRuntimeProfile] = {}

    def register_or_get(self, profile: PublicFeedRuntimeProfile) -> PublicFeedRuntimeProfile:
        with self._lock:
            existing = self._by_adapter.get(profile.adoption_profile.adapter_code)
            if existing is None:
                self._by_adapter[profile.adoption_profile.adapter_code] = profile
                return profile
            if existing != profile:
                raise ValueError("public feed runtime profile conflicts with existing adapter")
            return existing

    def get(self, adapter_code: str) -> PublicFeedRuntimeProfile | None:
        with self._lock:
            return self._by_adapter.get(adapter_code)


@dataclass(frozen=True, slots=True)
class PublicFeedActivationProjection:
    id: UUID
    feed_definition_id: UUID
    feed_code: str
    definition_version: int
    configuration_hash: str
    adapter_code: str
    schedule_id: UUID
    state: PublicFeedActivationState
    activated_at: datetime
    activated_by_actor_ref: str
    updated_at: datetime
    updated_by_actor_ref: str

    def __post_init__(self) -> None:
        _require_utc(self.activated_at, "activated_at")
        _require_utc(self.updated_at, "updated_at")
        _require_actor(self.activated_by_actor_ref, "activated_by_actor_ref")
        _require_actor(self.updated_by_actor_ref, "updated_by_actor_ref")

    @classmethod
    def create(
        cls,
        *,
        definition: CanonicalPublicFeedDefinition,
        schedule_id: UUID,
        actor_ref: str,
        at: datetime,
    ) -> PublicFeedActivationProjection:
        return cls(
            id=uuid5(
                _ACTIVATION_NAMESPACE,
                f"{definition.id}:{definition.configuration_hash}",
            ),
            feed_definition_id=definition.id,
            feed_code=definition.feed_code,
            definition_version=definition.definition_version,
            configuration_hash=definition.configuration_hash,
            adapter_code=definition.definition.adapter_code,
            schedule_id=schedule_id,
            state=PublicFeedActivationState.ACTIVE,
            activated_at=at,
            activated_by_actor_ref=actor_ref,
            updated_at=at,
            updated_by_actor_ref=actor_ref,
        )

    def transition(
        self,
        target: PublicFeedActivationState,
        *,
        actor_ref: str,
        at: datetime,
    ) -> PublicFeedActivationProjection:
        allowed = {
            PublicFeedActivationState.ACTIVE: {
                PublicFeedActivationState.PAUSED,
                PublicFeedActivationState.RETIRED,
            },
            PublicFeedActivationState.PAUSED: {
                PublicFeedActivationState.ACTIVE,
                PublicFeedActivationState.RETIRED,
            },
            PublicFeedActivationState.RETIRED: set(),
        }
        if target not in allowed[self.state]:
            raise ValueError(f"invalid activation transition {self.state} -> {target}")
        return replace(
            self,
            state=target,
            updated_at=at,
            updated_by_actor_ref=actor_ref,
        )


@dataclass(frozen=True, slots=True)
class PublicFeedAuditEvent:
    sequence: int
    definition_id: UUID
    activation_id: UUID | None
    action: PublicFeedAuditAction
    actor_ref: str
    occurred_at: datetime
    configuration_hash: str


class PublicFeedCatalogRepository(Protocol):
    def add_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition: ...

    def replace_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition: ...

    def get_definition(
        self,
        feed_code: str,
        definition_version: int,
    ) -> CanonicalPublicFeedDefinition | None: ...

    def get_latest(self, feed_code: str) -> CanonicalPublicFeedDefinition | None: ...

    def list_definitions(self) -> tuple[CanonicalPublicFeedDefinition, ...]: ...

    def add_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection: ...

    def replace_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection: ...

    def get_activation_for_definition(
        self,
        definition_id: UUID,
    ) -> PublicFeedActivationProjection | None: ...

    def append_audit(
        self,
        *,
        definition_id: UUID,
        activation_id: UUID | None,
        action: PublicFeedAuditAction,
        actor_ref: str,
        occurred_at: datetime,
        configuration_hash: str,
    ) -> PublicFeedAuditEvent: ...

    def list_audit(self, definition_id: UUID) -> tuple[PublicFeedAuditEvent, ...]: ...


class InMemoryPublicFeedCatalogRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._definitions: dict[tuple[str, int], CanonicalPublicFeedDefinition] = {}
        self._activations: dict[UUID, PublicFeedActivationProjection] = {}
        self._audit: list[PublicFeedAuditEvent] = []

    def add_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition:
        key = (definition.feed_code, definition.definition_version)
        with self._lock:
            existing = self._definitions.get(key)
            if existing is None:
                self._definitions[key] = definition
                return definition
            if existing != definition:
                raise ValueError("public feed definition identity conflict")
            return existing

    def replace_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition:
        key = (definition.feed_code, definition.definition_version)
        with self._lock:
            current = self._definitions.get(key)
            if current is None:
                raise KeyError("public feed definition not found")
            if (
                current.id != definition.id
                or current.configuration_hash != definition.configuration_hash
            ):
                raise ValueError("immutable public feed definition drift")
            self._definitions[key] = definition
            return definition

    def get_definition(
        self,
        feed_code: str,
        definition_version: int,
    ) -> CanonicalPublicFeedDefinition | None:
        with self._lock:
            return self._definitions.get((feed_code, definition_version))

    def get_latest(self, feed_code: str) -> CanonicalPublicFeedDefinition | None:
        with self._lock:
            values = [
                value for (code, _version), value in self._definitions.items() if code == feed_code
            ]
            return max(values, key=lambda item: item.definition_version) if values else None

    def list_definitions(self) -> tuple[CanonicalPublicFeedDefinition, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._definitions.values(),
                    key=lambda item: (item.feed_code, item.definition_version),
                )
            )

    def add_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection:
        with self._lock:
            existing = self._activations.get(activation.feed_definition_id)
            if existing is None:
                self._activations[activation.feed_definition_id] = activation
                return activation
            if existing != activation:
                raise ValueError("public feed activation identity conflict")
            return existing

    def replace_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection:
        with self._lock:
            current = self._activations.get(activation.feed_definition_id)
            if current is None:
                raise KeyError("public feed activation not found")
            if (
                current.id != activation.id
                or current.configuration_hash != activation.configuration_hash
            ):
                raise ValueError("immutable activation projection drift")
            self._activations[activation.feed_definition_id] = activation
            return activation

    def get_activation_for_definition(
        self,
        definition_id: UUID,
    ) -> PublicFeedActivationProjection | None:
        with self._lock:
            return self._activations.get(definition_id)

    def append_audit(
        self,
        *,
        definition_id: UUID,
        activation_id: UUID | None,
        action: PublicFeedAuditAction,
        actor_ref: str,
        occurred_at: datetime,
        configuration_hash: str,
    ) -> PublicFeedAuditEvent:
        with self._lock:
            event = PublicFeedAuditEvent(
                sequence=len(self._audit) + 1,
                definition_id=definition_id,
                activation_id=activation_id,
                action=action,
                actor_ref=actor_ref,
                occurred_at=occurred_at,
                configuration_hash=configuration_hash,
            )
            self._audit.append(event)
            return event

    def list_audit(self, definition_id: UUID) -> tuple[PublicFeedAuditEvent, ...]:
        with self._lock:
            return tuple(event for event in self._audit if event.definition_id == definition_id)


class CanonicalPublicFeedCatalogService:
    def __init__(
        self,
        *,
        repository: PublicFeedCatalogRepository,
        security: AdminSecurityService,
        provider_admission: SourceProviderAdmissionService,
        runtime_profiles: PublicFeedRuntimeProfileRegistry,
        scheduler: SourceAcquisitionSchedulerService,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._security = security
        self._provider_admission = provider_admission
        self._runtime_profiles = runtime_profiles
        self._scheduler = scheduler
        self._clock = clock

    def register_draft(
        self,
        principal: AdminPrincipal,
        *,
        definition_version: int,
        definition: PublicFeedDefinition,
        interval_seconds: int,
        max_dispatch_attempts: int,
    ) -> CanonicalPublicFeedDefinition:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        latest = self._repository.get_latest(definition.feed_code)
        expected_version = 1 if latest is None else latest.definition_version + 1
        if definition_version != expected_version:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_VERSION_CONFLICT",
                "Public feed definition version must be the next immutable version",
                409,
                meta={"expected_definition_version": expected_version},
            )
        created = CanonicalPublicFeedDefinition.create(
            definition_version=definition_version,
            definition=definition,
            interval_seconds=interval_seconds,
            max_dispatch_attempts=max_dispatch_attempts,
            created_at=self._clock(),
            created_by_actor_ref=principal.audit_actor_ref,
        )
        stored = self._repository.add_definition(created)
        self._repository.append_audit(
            definition_id=stored.id,
            activation_id=None,
            action=PublicFeedAuditAction.DRAFT_REGISTERED,
            actor_ref=principal.audit_actor_ref,
            occurred_at=stored.created_at,
            configuration_hash=stored.configuration_hash,
        )
        return stored

    def preflight(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> PublicFeedPreflightResult:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        definition = self._require_definition(feed_code, definition_version)
        if definition.state is not PublicFeedCatalogState.DRAFT:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_STATE_CONFLICT",
                "Only DRAFT public feed definitions may be preflighted",
                409,
            )
        runtime_profile = self._build_runtime_profile(definition)
        adoption = runtime_profile.adoption_profile
        command = runtime_profile.acquisition_command
        at = self._clock()
        updated = definition.mark_preflight(actor_ref=principal.audit_actor_ref, at=at)
        self._repository.replace_definition(updated)
        self._repository.append_audit(
            definition_id=updated.id,
            activation_id=None,
            action=PublicFeedAuditAction.PREFLIGHT_SUCCEEDED,
            actor_ref=principal.audit_actor_ref,
            occurred_at=at,
            configuration_hash=updated.configuration_hash,
        )
        return PublicFeedPreflightResult(
            feed_definition_id=updated.id,
            configuration_hash=updated.configuration_hash,
            adapter_code=adoption.adapter_code,
            external_locator=command.external_locator,
            allowed_origin=adoption.allowed_origins[0],
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            interval_seconds=updated.interval_seconds,
            max_dispatch_attempts=updated.max_dispatch_attempts,
        )

    def approve(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
        expected_configuration_hash: str,
    ) -> CanonicalPublicFeedDefinition:
        self._security.authorize(principal, AdminCapability.SOURCE_APPROVE)
        definition = self._require_definition(feed_code, definition_version)
        if definition.configuration_hash != expected_configuration_hash:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_HASH_CONFLICT",
                "Public feed definition hash changed before approval",
                409,
            )
        try:
            approved = definition.approve(
                actor_ref=principal.audit_actor_ref,
                at=self._clock(),
            )
        except ValueError as exc:
            code = (
                "ADMIN_SEPARATION_OF_DUTIES"
                if principal.audit_actor_ref == definition.created_by_actor_ref
                else "ADMIN_PUBLIC_FEED_STATE_CONFLICT"
            )
            raise DomainError(code, str(exc), 403 if code.endswith("DUTIES") else 409) from exc
        stored = self._repository.replace_definition(approved)
        self._repository.append_audit(
            definition_id=stored.id,
            activation_id=None,
            action=PublicFeedAuditAction.APPROVED,
            actor_ref=principal.audit_actor_ref,
            occurred_at=stored.approved_at or self._clock(),
            configuration_hash=stored.configuration_hash,
        )
        return stored

    def activate(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
        expected_configuration_hash: str,
        first_due_at: datetime,
    ) -> PublicFeedActivationProjection:
        self._security.authorize(principal, AdminCapability.SOURCE_ACTIVATE)
        definition = self._require_definition(feed_code, definition_version)
        if definition.state is not PublicFeedCatalogState.APPROVED:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_STATE_CONFLICT",
                "Only APPROVED public feed definitions may be activated",
                409,
            )
        if definition.configuration_hash != expected_configuration_hash:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_HASH_CONFLICT",
                "Public feed definition hash changed before activation",
                409,
            )
        _require_utc(first_due_at, "first_due_at")
        existing = self._repository.get_activation_for_definition(definition.id)
        if existing is not None:
            if existing.configuration_hash != expected_configuration_hash:
                raise DomainError(
                    "ADMIN_PUBLIC_FEED_ACTIVATION_CONFLICT",
                    "Existing activation belongs to another definition hash",
                    409,
                )
            return existing

        at = self._clock()
        capability = definition.definition.capability_template.instantiate(created_at=at)
        self._provider_admission.register(
            adapter_code=capability.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=capability.quota_limit,
            quota_window_seconds=capability.quota_window_seconds,
            failure_threshold=capability.failure_threshold,
            circuit_open_seconds=capability.circuit_open_seconds,
            permit_ttl_seconds=capability.permit_ttl_seconds,
            created_at=capability.created_at,
        )
        runtime_profile = self._runtime_profiles.register_or_get(
            self._build_runtime_profile(definition)
        )
        command = runtime_profile.acquisition_command
        schedule = self._scheduler.create_schedule(
            adapter_code=command.adapter_code,
            external_locator=command.external_locator,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            configuration_hash=command.configuration_hash,
            first_due_at=first_due_at,
            interval_seconds=definition.interval_seconds,
            max_dispatch_attempts=definition.max_dispatch_attempts,
            locale=command.context.locale,
            jurisdiction_code=command.context.jurisdiction_code,
            now=at,
        )
        projection = PublicFeedActivationProjection.create(
            definition=definition,
            schedule_id=schedule.id,
            actor_ref=principal.audit_actor_ref,
            at=at,
        )
        stored = self._repository.add_activation(projection)
        self._repository.append_audit(
            definition_id=definition.id,
            activation_id=stored.id,
            action=PublicFeedAuditAction.ACTIVATED,
            actor_ref=principal.audit_actor_ref,
            occurred_at=at,
            configuration_hash=definition.configuration_hash,
        )
        return stored

    def pause(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> PublicFeedActivationProjection:
        return self._transition_activation(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
            target=PublicFeedActivationState.PAUSED,
            action=PublicFeedAuditAction.PAUSED,
        )

    def resume(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> PublicFeedActivationProjection:
        return self._transition_activation(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
            target=PublicFeedActivationState.ACTIVE,
            action=PublicFeedAuditAction.RESUMED,
        )

    def retire_activation(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> PublicFeedActivationProjection:
        return self._transition_activation(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
            target=PublicFeedActivationState.RETIRED,
            action=PublicFeedAuditAction.ACTIVATION_RETIRED,
        )

    def retire_definition(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> CanonicalPublicFeedDefinition:
        self._security.authorize(principal, AdminCapability.SOURCE_APPROVE)
        definition = self._require_definition(feed_code, definition_version)
        activation = self._repository.get_activation_for_definition(definition.id)
        if activation is not None and activation.state is not PublicFeedActivationState.RETIRED:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_STATE_CONFLICT",
                "Active projection must be retired before definition retirement",
                409,
            )
        at = self._clock()
        try:
            retired = definition.retire(actor_ref=principal.audit_actor_ref, at=at)
        except ValueError as exc:
            raise DomainError("ADMIN_PUBLIC_FEED_STATE_CONFLICT", str(exc), 409) from exc
        stored = self._repository.replace_definition(retired)
        self._repository.append_audit(
            definition_id=stored.id,
            activation_id=activation.id if activation else None,
            action=PublicFeedAuditAction.DEFINITION_RETIRED,
            actor_ref=principal.audit_actor_ref,
            occurred_at=at,
            configuration_hash=stored.configuration_hash,
        )
        return stored

    def list_definitions(
        self,
        principal: AdminPrincipal,
    ) -> tuple[CanonicalPublicFeedDefinition, ...]:
        self._security.authorize_any(
            principal,
            frozenset(
                {
                    AdminCapability.SOURCE_MANAGE,
                    AdminCapability.SOURCE_APPROVE,
                    AdminCapability.SOURCE_ACTIVATE,
                }
            ),
        )
        return self._repository.list_definitions()

    def audit(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
    ) -> tuple[PublicFeedAuditEvent, ...]:
        self._security.authorize(principal, AdminCapability.AUDIT_READ)
        definition = self._require_definition(feed_code, definition_version)
        return self._repository.list_audit(definition.id)

    def _transition_activation(
        self,
        principal: AdminPrincipal,
        *,
        feed_code: str,
        definition_version: int,
        target: PublicFeedActivationState,
        action: PublicFeedAuditAction,
    ) -> PublicFeedActivationProjection:
        self._security.authorize(principal, AdminCapability.SOURCE_ACTIVATE)
        definition = self._require_definition(feed_code, definition_version)
        activation = self._repository.get_activation_for_definition(definition.id)
        if activation is None:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_ACTIVATION_NOT_FOUND",
                "Public feed activation projection not found",
                404,
            )
        at = self._clock()
        try:
            if target is PublicFeedActivationState.PAUSED:
                self._provider_admission.pause(activation.adapter_code, at=at)
                self._scheduler.pause(activation.schedule_id, now=at)
            elif target is PublicFeedActivationState.ACTIVE:
                self._provider_admission.resume(activation.adapter_code, at=at)
                self._scheduler.resume(activation.schedule_id, now=at)
            else:
                self._scheduler.retire(activation.schedule_id, now=at)
                self._provider_admission.retire(activation.adapter_code, at=at)
            updated = activation.transition(
                target,
                actor_ref=principal.audit_actor_ref,
                at=at,
            )
        except ValueError as exc:
            raise DomainError("ADMIN_PUBLIC_FEED_STATE_CONFLICT", str(exc), 409) from exc
        stored = self._repository.replace_activation(updated)
        self._repository.append_audit(
            definition_id=definition.id,
            activation_id=stored.id,
            action=action,
            actor_ref=principal.audit_actor_ref,
            occurred_at=at,
            configuration_hash=definition.configuration_hash,
        )
        return stored

    def _require_definition(
        self,
        feed_code: str,
        definition_version: int,
    ) -> CanonicalPublicFeedDefinition:
        definition = self._repository.get_definition(feed_code, definition_version)
        if definition is None:
            raise DomainError(
                "ADMIN_PUBLIC_FEED_NOT_FOUND",
                "Public feed definition not found",
                404,
            )
        return definition

    @staticmethod
    def _build_runtime_profile(
        definition: CanonicalPublicFeedDefinition,
    ) -> PublicFeedRuntimeProfile:
        public = definition.definition
        adoption = public.to_adoption_profile()
        capture = StrictRssAtomCaptureDefinition(
            adapter_code=public.adapter_code,
            profile=public.parser_profile,
        )
        command = public.acquisition_command()
        return PublicFeedRuntimeProfile(
            feed_definition_id=definition.id,
            configuration_hash=definition.configuration_hash,
            adoption_profile=adoption,
            capture_definition=capture,
            acquisition_command=command,
        )


__all__ = [
    "CanonicalPublicFeedCatalogService",
    "CanonicalPublicFeedDefinition",
    "InMemoryPublicFeedCatalogRepository",
    "InMemoryPublicFeedRuntimeProfileRegistry",
    "PublicFeedActivationProjection",
    "PublicFeedActivationState",
    "PublicFeedAuditAction",
    "PublicFeedAuditEvent",
    "PublicFeedCatalogRepository",
    "PublicFeedCatalogState",
    "PublicFeedPreflightResult",
    "PublicFeedRuntimeProfile",
    "PublicFeedRuntimeProfileRegistry",
]

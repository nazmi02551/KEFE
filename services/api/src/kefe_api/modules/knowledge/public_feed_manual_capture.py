from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_catalog import (
    PublicFeedCatalogRepository,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionOutcome,
    SourceAcquisitionResult,
)

_TRACE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_TERMINAL_OUTCOMES = frozenset(item.value for item in SourceAcquisitionOutcome)


@dataclass(frozen=True, slots=True)
class PublicFeedManualCaptureAuditEntry:
    event_id: UUID
    execution_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    configuration_hash: str
    actor_ref: str
    trace_id: str
    outcome: str
    source_artifact_id: UUID | None
    ingestion_run_id: UUID | None
    duration_ms: int
    error_code: str | None
    occurred_at: datetime

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.feed_code, "feed_code"),
            (self.configuration_hash, "configuration_hash"),
            (self.actor_ref, "actor_ref"),
            (self.trace_id, "trace_id"),
            (self.outcome, "outcome"),
        ):
            if not value or value != value.strip():
                raise ValueError(f"{field_name} must be exact nonblank text")
        if _TRACE_ID.fullmatch(self.trace_id) is None:
            raise ValueError("trace_id is invalid")
        if self.outcome not in {"ATTEMPT_STARTED", *_TERMINAL_OUTCOMES}:
            raise ValueError("manual capture audit outcome is invalid")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        _require_utc(self.occurred_at, "occurred_at")
        if self.outcome == "ATTEMPT_STARTED":
            if any(
                value is not None
                for value in (
                    self.source_artifact_id,
                    self.ingestion_run_id,
                    self.error_code,
                )
            ) or self.duration_ms != 0:
                raise ValueError("started audit cannot contain terminal result fields")
        elif self.error_code is not None:
            if not self.error_code.strip() or len(self.error_code) > 128:
                raise ValueError("error_code is invalid")


class PublicFeedManualCaptureAuditRepository(Protocol):
    def append(self, entry: PublicFeedManualCaptureAuditEntry) -> None: ...

    def list_entries(
        self,
        catalog_entry_id: UUID | None = None,
    ) -> tuple[PublicFeedManualCaptureAuditEntry, ...]: ...


class InMemoryPublicFeedManualCaptureAuditRepository:
    def __init__(self) -> None:
        self._entries: list[PublicFeedManualCaptureAuditEntry] = []
        self._event_ids: set[UUID] = set()
        self._lock = Lock()

    def append(self, entry: PublicFeedManualCaptureAuditEntry) -> None:
        with self._lock:
            if entry.event_id in self._event_ids:
                raise ValueError("duplicate manual capture audit event")
            self._event_ids.add(entry.event_id)
            self._entries.append(entry)

    def list_entries(
        self,
        catalog_entry_id: UUID | None = None,
    ) -> tuple[PublicFeedManualCaptureAuditEntry, ...]:
        with self._lock:
            return tuple(
                item
                for item in self._entries
                if catalog_entry_id is None
                or item.catalog_entry_id == catalog_entry_id
            )


class PublicFeedManualCaptureRuntime(Protocol):
    def execute(
        self,
        *,
        definition: PublicFeedDefinition,
        trace_id: str,
        at: datetime,
    ) -> SourceAcquisitionResult: ...


@dataclass(frozen=True, slots=True)
class PublicFeedManualCaptureExecutionResult:
    execution_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    configuration_hash: str
    trace_id: str
    outcome: SourceAcquisitionOutcome
    source_artifact_id: UUID | None
    ingestion_run_id: UUID | None
    duration_ms: int
    error_code: str | None

    def __post_init__(self) -> None:
        if _TRACE_ID.fullmatch(self.trace_id) is None:
            raise ValueError("trace_id is invalid")
        if type(self.outcome) is not SourceAcquisitionOutcome:
            raise ValueError("outcome must be exact SourceAcquisitionOutcome")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")


class ApprovedPublicFeedManualCaptureService:
    def __init__(
        self,
        *,
        catalog: PublicFeedCatalogRepository,
        runtime: PublicFeedManualCaptureRuntime,
        audit: PublicFeedManualCaptureAuditRepository,
        security: AdminSecurityService,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._catalog = catalog
        self._runtime = runtime
        self._audit = audit
        self._security = security
        self._clock = clock

    def capture_once(
        self,
        principal: AdminPrincipal,
        *,
        catalog_entry_id: UUID,
        trace_id: str | None = None,
    ) -> PublicFeedManualCaptureExecutionResult:
        now = self._clock()
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_MANAGE,
            now=now,
        )
        self._security.require_fresh_step_up(principal, now=now)
        entry = self._catalog.get(catalog_entry_id)
        if entry is None:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_NOT_FOUND",
                "Public feed catalog entry was not found",
                404,
            )
        if entry.state is not PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED:
            raise DomainError(
                "PUBLIC_FEED_MANUAL_CAPTURE_NOT_APPROVED",
                "Public feed is not approved for manual capture",
                409,
            )
        if entry.configuration_hash != entry.definition.configuration_hash:
            raise DomainError(
                "PUBLIC_FEED_MANUAL_CAPTURE_DEFINITION_INVALID",
                "Public feed definition integrity check failed",
                409,
            )
        resolved_trace_id = trace_id or str(uuid4())
        if _TRACE_ID.fullmatch(resolved_trace_id) is None:
            raise DomainError(
                "PUBLIC_FEED_MANUAL_CAPTURE_TRACE_INVALID",
                "Manual capture trace ID is invalid",
                422,
            )
        execution_id = uuid4()
        started = PublicFeedManualCaptureAuditEntry(
            event_id=uuid4(),
            execution_id=execution_id,
            catalog_entry_id=entry.id,
            feed_code=entry.feed_code,
            configuration_hash=entry.configuration_hash,
            actor_ref=principal.audit_actor_ref,
            trace_id=resolved_trace_id,
            outcome="ATTEMPT_STARTED",
            source_artifact_id=None,
            ingestion_run_id=None,
            duration_ms=0,
            error_code=None,
            occurred_at=now,
        )
        try:
            self._audit.append(started)
        except Exception as exc:
            raise DomainError(
                "PUBLIC_FEED_MANUAL_CAPTURE_AUDIT_UNAVAILABLE",
                "Manual capture audit is unavailable",
                503,
            ) from exc

        try:
            acquisition = self._runtime.execute(
                definition=entry.definition,
                trace_id=resolved_trace_id,
                at=now,
            )
            self._validate_result(entry.definition, acquisition, resolved_trace_id)
        except Exception:
            acquisition = SourceAcquisitionResult(
                outcome=SourceAcquisitionOutcome.FINAL_FAILURE,
                adapter_code=entry.adapter_code,
                pipeline_code=entry.definition.acquisition_command().pipeline_code,
                pipeline_version=entry.definition.acquisition_command().pipeline_version,
                trace_id=resolved_trace_id,
                duration_ms=0,
                error_code="PUBLIC_FEED_MANUAL_CAPTURE_UNEXPECTED",
            )

        terminal = PublicFeedManualCaptureAuditEntry(
            event_id=uuid4(),
            execution_id=execution_id,
            catalog_entry_id=entry.id,
            feed_code=entry.feed_code,
            configuration_hash=entry.configuration_hash,
            actor_ref=principal.audit_actor_ref,
            trace_id=resolved_trace_id,
            outcome=acquisition.outcome.value,
            source_artifact_id=acquisition.source_artifact_id,
            ingestion_run_id=acquisition.ingestion_run_id,
            duration_ms=acquisition.duration_ms,
            error_code=acquisition.error_code,
            occurred_at=self._clock(),
        )
        try:
            self._audit.append(terminal)
        except Exception as exc:
            raise DomainError(
                "PUBLIC_FEED_MANUAL_CAPTURE_AUDIT_UNAVAILABLE",
                "Manual capture terminal audit is unavailable",
                503,
                meta={"execution_id": str(execution_id)},
            ) from exc
        return PublicFeedManualCaptureExecutionResult(
            execution_id=execution_id,
            catalog_entry_id=entry.id,
            feed_code=entry.feed_code,
            configuration_hash=entry.configuration_hash,
            trace_id=resolved_trace_id,
            outcome=acquisition.outcome,
            source_artifact_id=acquisition.source_artifact_id,
            ingestion_run_id=acquisition.ingestion_run_id,
            duration_ms=acquisition.duration_ms,
            error_code=acquisition.error_code,
        )

    def list_audit(
        self,
        principal: AdminPrincipal,
        catalog_entry_id: UUID | None = None,
    ) -> tuple[PublicFeedManualCaptureAuditEntry, ...]:
        now = self._clock()
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_MANAGE,
            now=now,
        )
        if catalog_entry_id is not None and self._catalog.get(catalog_entry_id) is None:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_NOT_FOUND",
                "Public feed catalog entry was not found",
                404,
            )
        return self._audit.list_entries(catalog_entry_id)

    @staticmethod
    def _validate_result(
        definition: PublicFeedDefinition,
        result: SourceAcquisitionResult,
        trace_id: str,
    ) -> None:
        command = definition.acquisition_command()
        if type(result) is not SourceAcquisitionResult:
            raise ValueError("manual capture runtime returned invalid result")
        if (
            result.adapter_code != definition.adapter_code
            or result.pipeline_code != command.pipeline_code
            or result.pipeline_version != command.pipeline_version
            or result.trace_id != trace_id
        ):
            raise ValueError("manual capture runtime result identity mismatch")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


__all__ = [
    "ApprovedPublicFeedManualCaptureService",
    "InMemoryPublicFeedManualCaptureAuditRepository",
    "PublicFeedManualCaptureAuditEntry",
    "PublicFeedManualCaptureAuditRepository",
    "PublicFeedManualCaptureExecutionResult",
    "PublicFeedManualCaptureRuntime",
]

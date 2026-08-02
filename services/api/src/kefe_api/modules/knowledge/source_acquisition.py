from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from time import monotonic_ns
from types import MappingProxyType
from typing import Protocol
from uuid import UUID, uuid4

from kefe_api.modules.ingestion_orchestration.models import InputArtifactKind, utcnow
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.ports import KnowledgeRepository

_VERSIONED_ADAPTER_CODE = re.compile(
    r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*\.v[1-9][0-9]*$"
)


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def require_versioned_adapter_code(adapter_code: str) -> None:
    _require_text(adapter_code, "adapter_code")
    if _VERSIONED_ADAPTER_CODE.fullmatch(adapter_code) is None:
        raise ValueError(
            "adapter_code must be an immutable versioned identifier ending in .vN"
        )


@dataclass(frozen=True, slots=True)
class CapturedSource:
    content_hash: str
    external_id: str | None = None
    canonical_url: str | None = None
    publisher_or_issuer: str | None = None
    published_at: datetime | None = None
    language_code: str | None = None
    jurisdiction_code: str | None = None
    raw_storage_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.content_hash, "content_hash")
        for value, field_name in (
            (self.external_id, "external_id"),
            (self.canonical_url, "canonical_url"),
            (self.publisher_or_issuer, "publisher_or_issuer"),
            (self.language_code, "language_code"),
            (self.jurisdiction_code, "jurisdiction_code"),
            (self.raw_storage_ref, "raw_storage_ref"),
        ):
            if value is not None:
                _require_text(value, field_name)


@dataclass(frozen=True, slots=True)
class RetryableSourceCaptureError(Exception):
    code: str

    def __post_init__(self) -> None:
        _require_text(self.code, "code")


@dataclass(frozen=True, slots=True)
class FinalSourceCaptureError(Exception):
    code: str

    def __post_init__(self) -> None:
        _require_text(self.code, "code")


class SourceCaptureAdapter(Protocol):
    @property
    def adapter_code(self) -> str: ...

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
    ) -> CapturedSource: ...


class SourceCaptureRegistry(Protocol):
    def get(self, adapter_code: str) -> SourceCaptureAdapter: ...


class InMemorySourceCaptureRegistry:
    def __init__(self, adapters: tuple[SourceCaptureAdapter, ...] = ()) -> None:
        adapter_map: dict[str, SourceCaptureAdapter] = {}
        for adapter in adapters:
            require_versioned_adapter_code(adapter.adapter_code)
            if adapter.adapter_code in adapter_map:
                raise ValueError("duplicate source capture adapter code")
            adapter_map[adapter.adapter_code] = adapter
        self._adapters = MappingProxyType(adapter_map)

    def get(self, adapter_code: str) -> SourceCaptureAdapter:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._adapters[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc


@dataclass(frozen=True, slots=True)
class SourceAcquisitionCommand:
    adapter_code: str
    external_locator: str
    pipeline_code: str
    pipeline_version: str
    configuration_hash: str
    taxonomy_version: str | None = None
    methodology_version: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        for value, field_name in (
            (self.external_locator, "external_locator"),
            (self.pipeline_code, "pipeline_code"),
            (self.pipeline_version, "pipeline_version"),
            (self.configuration_hash, "configuration_hash"),
        ):
            _require_text(value, field_name)
        for value, field_name in (
            (self.taxonomy_version, "taxonomy_version"),
            (self.methodology_version, "methodology_version"),
            (self.locale, "locale"),
            (self.jurisdiction_code, "jurisdiction_code"),
        ):
            if value is not None:
                _require_text(value, field_name)


class SourceAcquisitionOutcome(StrEnum):
    ADMITTED = "ADMITTED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    FINAL_FAILURE = "FINAL_FAILURE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class SourceAcquisitionResult:
    outcome: SourceAcquisitionOutcome
    adapter_code: str
    pipeline_code: str
    pipeline_version: str
    trace_id: str
    duration_ms: int
    source_artifact_id: UUID | None = None
    ingestion_run_id: UUID | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        _require_text(self.pipeline_code, "pipeline_code")
        _require_text(self.pipeline_version, "pipeline_version")
        _require_text(self.trace_id, "trace_id")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        if self.error_code is not None:
            _require_text(self.error_code, "error_code")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "adapter_code": self.adapter_code,
            "pipeline_code": self.pipeline_code,
            "pipeline_version": self.pipeline_version,
            "trace_id": self.trace_id,
            "source_artifact_id": (
                str(self.source_artifact_id)
                if self.source_artifact_id is not None
                else None
            ),
            "ingestion_run_id": (
                str(self.ingestion_run_id)
                if self.ingestion_run_id is not None
                else None
            ),
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
        }


class SourceAcquisitionObserver(Protocol):
    def record(self, result: SourceAcquisitionResult) -> None: ...


class NoOpSourceAcquisitionObserver:
    def record(self, result: SourceAcquisitionResult) -> None:
        del result


class InMemorySourceAcquisitionObserver:
    def __init__(self) -> None:
        self.results: list[SourceAcquisitionResult] = []

    def record(self, result: SourceAcquisitionResult) -> None:
        self.results.append(result)


class SourceAcquisitionService:
    def __init__(
        self,
        *,
        knowledge_repository: KnowledgeRepository,
        ingestion_service: IngestionOrchestrationService,
        registry: SourceCaptureRegistry,
        observer: SourceAcquisitionObserver,
        clock=utcnow,
        monotonic_clock=monotonic_ns,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._ingestion_service = ingestion_service
        self._registry = registry
        self._observer = observer
        self._clock = clock
        self._monotonic_clock = monotonic_clock

    def acquire(
        self,
        command: SourceAcquisitionCommand,
        *,
        trace_id: str | None = None,
        before_artifact_persist: Callable[[], None] | None = None,
        before_run_admission: Callable[[], None] | None = None,
    ) -> SourceAcquisitionResult:
        started_ns = self._monotonic_clock()
        resolved_trace_id = trace_id or str(uuid4())
        try:
            adapter = self._registry.get(command.adapter_code)
        except KeyError:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.BLOCKED,
                    error_code="SOURCE_CAPTURE_ADAPTER_NOT_REGISTERED",
                )
            )

        try:
            captured = adapter.capture(
                external_locator=command.external_locator,
                trace_id=resolved_trace_id,
            )
            if not isinstance(captured, CapturedSource):
                raise FinalSourceCaptureError("SOURCE_CAPTURE_CONTRACT_INVALID")
        except RetryableSourceCaptureError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.RETRYABLE_FAILURE,
                    error_code=exc.code,
                )
            )
        except FinalSourceCaptureError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.FINAL_FAILURE,
                    error_code=exc.code,
                )
            )
        except Exception:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.FINAL_FAILURE,
                    error_code="UNEXPECTED_SOURCE_CAPTURE_FAILURE",
                )
            )

        if before_artifact_persist is not None:
            before_artifact_persist()
        try:
            artifact = self._knowledge_repository.add_source_artifact(
                SourceArtifact.create(
                    adapter_code=command.adapter_code,
                    external_locator=command.external_locator,
                    captured_at=self._clock(),
                    content_hash=captured.content_hash,
                    external_id=captured.external_id,
                    canonical_url=captured.canonical_url,
                    publisher_or_issuer=captured.publisher_or_issuer,
                    published_at=captured.published_at,
                    language_code=captured.language_code,
                    jurisdiction_code=captured.jurisdiction_code,
                    raw_storage_ref=captured.raw_storage_ref,
                )
            )
        except ValueError:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.FINAL_FAILURE,
                    error_code="SOURCE_ACQUISITION_ADMISSION_INVALID",
                )
            )
        except Exception:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.RETRYABLE_FAILURE,
                    error_code="SOURCE_ACQUISITION_ADMISSION_RETRYABLE",
                )
            )

        if before_run_admission is not None:
            before_run_admission()
        try:
            run = self._ingestion_service.start_run(
                input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
                input_artifact_id=artifact.id,
                input_content_hash=artifact.content_hash,
                pipeline_code=command.pipeline_code,
                pipeline_version=command.pipeline_version,
                configuration_hash=command.configuration_hash,
                taxonomy_version=command.taxonomy_version,
                methodology_version=command.methodology_version,
                locale=command.locale,
                jurisdiction_code=(
                    command.jurisdiction_code or artifact.jurisdiction_code
                ),
            )
        except ValueError:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.FINAL_FAILURE,
                    error_code="SOURCE_ACQUISITION_ADMISSION_INVALID",
                )
            )
        except Exception:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    command=command,
                    trace_id=resolved_trace_id,
                    outcome=SourceAcquisitionOutcome.RETRYABLE_FAILURE,
                    error_code="SOURCE_ACQUISITION_ADMISSION_RETRYABLE",
                )
            )

        return self._emit(
            self._result(
                started_ns=started_ns,
                command=command,
                trace_id=resolved_trace_id,
                outcome=SourceAcquisitionOutcome.ADMITTED,
                source_artifact_id=artifact.id,
                ingestion_run_id=run.id,
            )
        )

    def _result(
        self,
        *,
        started_ns: int,
        command: SourceAcquisitionCommand,
        trace_id: str,
        outcome: SourceAcquisitionOutcome,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceAcquisitionResult:
        elapsed_ns = max(0, self._monotonic_clock() - started_ns)
        return SourceAcquisitionResult(
            outcome=outcome,
            adapter_code=command.adapter_code,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            trace_id=trace_id,
            source_artifact_id=source_artifact_id,
            ingestion_run_id=ingestion_run_id,
            duration_ms=elapsed_ns // 1_000_000,
            error_code=error_code,
        )

    def _emit(self, result: SourceAcquisitionResult) -> SourceAcquisitionResult:
        try:
            self._observer.record(result)
        except Exception:
            pass
        return result

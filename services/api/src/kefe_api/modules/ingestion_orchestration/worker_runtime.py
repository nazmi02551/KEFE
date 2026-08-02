from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, Protocol
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    require_text,
)
from kefe_api.modules.ingestion_orchestration.ports import StageProcessor


class IngestionWorkerRunOutcome(StrEnum):
    IDLE = "IDLE"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    FINAL_FAILURE = "FINAL_FAILURE"
    LEASE_LOST = "LEASE_LOST"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class IngestionRuntimeStage:
    stage_code: str
    stage_version: str
    max_attempts: int
    executor_kind: ExecutorKind

    def __post_init__(self) -> None:
        require_text(self.stage_code, "stage_code")
        require_text(self.stage_version, "stage_version")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

    @property
    def identity(self) -> tuple[str, str]:
        return self.stage_code, self.stage_version


@dataclass(frozen=True, slots=True)
class IngestionRuntimePlan:
    pipeline_code: str
    pipeline_version: str
    stages: tuple[IngestionRuntimeStage, ...]

    def __post_init__(self) -> None:
        require_text(self.pipeline_code, "pipeline_code")
        require_text(self.pipeline_version, "pipeline_version")
        if not self.stages:
            raise ValueError("ingestion runtime plan requires at least one stage")
        identities = tuple(stage.identity for stage in self.stages)
        if len(set(identities)) != len(identities):
            raise ValueError("ingestion runtime plan contains duplicate stage identity")

    @property
    def identity(self) -> tuple[str, str]:
        return self.pipeline_code, self.pipeline_version

    @property
    def stage_identities(self) -> frozenset[tuple[str, str]]:
        return frozenset(stage.identity for stage in self.stages)


class IngestionWorkerRuntimeRegistry(Protocol):
    def get_plan(
        self,
        *,
        pipeline_code: str,
        pipeline_version: str,
    ) -> IngestionRuntimePlan: ...

    def get_processor(
        self,
        *,
        pipeline_code: str,
        pipeline_version: str,
        stage_code: str,
        stage_version: str,
    ) -> StageProcessor: ...


class InMemoryIngestionWorkerRuntimeRegistry:
    def __init__(
        self,
        plans: tuple[IngestionRuntimePlan, ...] = (),
        processors: Mapping[tuple[str, str, str, str], StageProcessor] | None = None,
    ) -> None:
        plan_map: dict[tuple[str, str], IngestionRuntimePlan] = {}
        for plan in plans:
            if plan.identity in plan_map:
                raise ValueError("duplicate ingestion runtime plan identity")
            plan_map[plan.identity] = plan

        processor_map = dict(processors or {})
        for key in processor_map:
            if len(key) != 4 or any(not value.strip() for value in key):
                raise ValueError("processor registry keys must be four nonblank strings")
        for plan in plans:
            for stage in plan.stages:
                key = (
                    plan.pipeline_code,
                    plan.pipeline_version,
                    stage.stage_code,
                    stage.stage_version,
                )
                if key not in processor_map:
                    raise ValueError(
                        "every runtime plan stage requires an exact registered processor"
                    )

        self._plans = MappingProxyType(plan_map)
        self._processors = MappingProxyType(processor_map)

    def get_plan(
        self,
        *,
        pipeline_code: str,
        pipeline_version: str,
    ) -> IngestionRuntimePlan:
        require_text(pipeline_code, "pipeline_code")
        require_text(pipeline_version, "pipeline_version")
        try:
            return self._plans[(pipeline_code, pipeline_version)]
        except KeyError as exc:
            raise KeyError((pipeline_code, pipeline_version)) from exc

    def get_processor(
        self,
        *,
        pipeline_code: str,
        pipeline_version: str,
        stage_code: str,
        stage_version: str,
    ) -> StageProcessor:
        key = (pipeline_code, pipeline_version, stage_code, stage_version)
        try:
            return self._processors[key]
        except KeyError as exc:
            raise KeyError(key) from exc


@dataclass(frozen=True, slots=True)
class IngestionWorkerRunResult:
    outcome: IngestionWorkerRunOutcome
    worker_ref: str
    pipeline_code: str
    pipeline_version: str
    trace_id: str
    duration_ms: int
    run_id: UUID | None = None
    lease_id: UUID | None = None
    stage_code: str | None = None
    stage_version: str | None = None
    completed_stage_count: int = 0
    stage_attempt: int | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        require_text(self.worker_ref, "worker_ref")
        require_text(self.pipeline_code, "pipeline_code")
        require_text(self.pipeline_version, "pipeline_version")
        require_text(self.trace_id, "trace_id")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        if self.completed_stage_count < 0:
            raise ValueError("completed_stage_count must be >= 0")
        if self.stage_attempt is not None and self.stage_attempt < 1:
            raise ValueError("stage_attempt must be >= 1")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "worker_ref": self.worker_ref,
            "pipeline_code": self.pipeline_code,
            "pipeline_version": self.pipeline_version,
            "trace_id": self.trace_id,
            "run_id": str(self.run_id) if self.run_id is not None else None,
            "lease_id": str(self.lease_id) if self.lease_id is not None else None,
            "stage_code": self.stage_code,
            "stage_version": self.stage_version,
            "completed_stage_count": self.completed_stage_count,
            "stage_attempt": self.stage_attempt,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
        }


class IngestionWorkerObserver(Protocol):
    def record(self, result: IngestionWorkerRunResult) -> None: ...


class NoOpIngestionWorkerObserver:
    def record(self, result: IngestionWorkerRunResult) -> None:
        del result


class InMemoryIngestionWorkerObserver:
    def __init__(self) -> None:
        self.results: list[IngestionWorkerRunResult] = []

    def record(self, result: IngestionWorkerRunResult) -> None:
        self.results.append(result)

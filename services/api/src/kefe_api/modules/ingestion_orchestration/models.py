from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any
from uuid import UUID


class InputArtifactKind(StrEnum):
    SOURCE_ARTIFACT = "SOURCE_ARTIFACT"
    NORMALIZED_ARTIFACT = "NORMALIZED_ARTIFACT"


class IngestionRunState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CANCELED = "CANCELED"


class ExecutorKind(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    AI_ASSISTED = "AI_ASSISTED"
    HUMAN_ASSISTED = "HUMAN_ASSISTED"
    EXTERNAL_CAPABILITY = "EXTERNAL_CAPABILITY"


class StageOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"


class ProposalReviewDecisionKind(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


MATERIALIZABLE_KNOWLEDGE_KINDS = frozenset(
    {
        "CLAIM",
        "CLAIM_ASSESSMENT",
        "CLAIM_ASSERTION",
        "EVIDENCE_LINK",
        "CLAIM_RELATION",
        "ARGUMENT",
        "ARGUMENT_RELATION",
    }
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def stable_payload_hash(payload: dict[str, Any]) -> str:
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(encoded).hexdigest()


def build_run_key(
    *,
    input_artifact_kind: InputArtifactKind,
    input_artifact_id: UUID,
    input_content_hash: str,
    pipeline_code: str,
    pipeline_version: str,
    configuration_hash: str,
    taxonomy_version: str | None = None,
    methodology_version: str | None = None,
    locale: str | None = None,
    jurisdiction_code: str | None = None,
) -> str:
    parts = (
        input_artifact_kind.value,
        str(input_artifact_id),
        input_content_hash,
        pipeline_code,
        pipeline_version,
        configuration_hash,
        taxonomy_version or "",
        methodology_version or "",
        locale or "",
        jurisdiction_code or "",
    )
    return sha256("\x1f".join(parts).encode()).hexdigest()


_ALLOWED_TRANSITIONS: dict[IngestionRunState, frozenset[IngestionRunState]] = {
    IngestionRunState.QUEUED: frozenset(
        {IngestionRunState.RUNNING, IngestionRunState.CANCELED}
    ),
    IngestionRunState.RUNNING: frozenset(
        {
            IngestionRunState.QUEUED,
            IngestionRunState.SUCCEEDED,
            IngestionRunState.FAILED_RETRYABLE,
            IngestionRunState.FAILED_FINAL,
            IngestionRunState.CANCELED,
        }
    ),
    IngestionRunState.FAILED_RETRYABLE: frozenset(
        {IngestionRunState.QUEUED, IngestionRunState.CANCELED}
    ),
    IngestionRunState.SUCCEEDED: frozenset(),
    IngestionRunState.FAILED_FINAL: frozenset(),
    IngestionRunState.CANCELED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class IngestionRun:
    id: UUID
    run_key: str
    input_artifact_kind: InputArtifactKind
    input_artifact_id: UUID
    input_content_hash: str
    pipeline_code: str
    pipeline_version: str
    configuration_hash: str
    state: IngestionRunState
    created_at: datetime
    updated_at: datetime
    taxonomy_version: str | None = None
    methodology_version: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.run_key, "run_key"),
            (self.input_content_hash, "input_content_hash"),
            (self.pipeline_code, "pipeline_code"),
            (self.pipeline_version, "pipeline_version"),
            (self.configuration_hash, "configuration_hash"),
        ):
            require_text(value, field_name)

    def transition(
        self,
        target: IngestionRunState,
        *,
        at: datetime | None = None,
    ) -> IngestionRun:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid ingestion run transition: {self.state} -> {target}")
        return replace(self, state=target, updated_at=at or utcnow())


@dataclass(frozen=True, slots=True)
class StageExecution:
    id: UUID
    run_id: UUID
    stage_code: str
    stage_version: str
    attempt_no: int
    max_attempts: int
    executor_kind: ExecutorKind
    input_hash: str
    started_at: datetime
    outcome: StageOutcome
    output_hash: str | None = None
    error_code: str | None = None
    completed_at: datetime | None = None
    execution_ref: str | None = None
    trace_id: str | None = None

    def __post_init__(self) -> None:
        require_text(self.stage_code, "stage_code")
        require_text(self.stage_version, "stage_version")
        require_text(self.input_hash, "input_hash")
        if self.attempt_no < 1:
            raise ValueError("attempt_no must be >= 1")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.attempt_no > self.max_attempts:
            raise ValueError("attempt_no cannot exceed max_attempts")
        if self.outcome is StageOutcome.SUCCEEDED and not self.output_hash:
            raise ValueError("successful stage execution requires output_hash")
        if self.outcome is not StageOutcome.SUCCEEDED and not self.error_code:
            raise ValueError("failed stage execution requires error_code")
        if self.outcome is StageOutcome.FAILED_RETRYABLE and not self.may_retry:
            raise ValueError("retryable outcome cannot be recorded after retry limit")

    @property
    def may_retry(self) -> bool:
        return self.attempt_no < self.max_attempts


@dataclass(frozen=True, slots=True)
class ProposalDraft:
    proposal_kind: str
    payload_schema_ref: str
    payload_schema_version: str
    payload: dict[str, Any]
    taxonomy_version: str | None = None
    configuration_version: str | None = None
    methodology_version: str | None = None
    confidence: float | None = None
    risk_code: str | None = None
    ai_execution_ref: str | None = None
    provenance_ref: str | None = None
    supersedes_proposal_id: UUID | None = None

    def __post_init__(self) -> None:
        require_text(self.proposal_kind, "proposal_kind")
        require_text(self.payload_schema_ref, "payload_schema_ref")
        require_text(self.payload_schema_version, "payload_schema_version")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Proposal:
    id: UUID
    proposal_kind: str
    payload_schema_ref: str
    payload_schema_version: str
    payload: dict[str, Any]
    payload_hash: str
    run_id: UUID
    stage_execution_id: UUID
    created_at: datetime
    taxonomy_version: str | None = None
    configuration_version: str | None = None
    methodology_version: str | None = None
    confidence: float | None = None
    risk_code: str | None = None
    ai_execution_ref: str | None = None
    provenance_ref: str | None = None
    supersedes_proposal_id: UUID | None = None

    def __post_init__(self) -> None:
        require_text(self.proposal_kind, "proposal_kind")
        require_text(self.payload_schema_ref, "payload_schema_ref")
        require_text(self.payload_schema_version, "payload_schema_version")
        require_text(self.payload_hash, "payload_hash")
        if stable_payload_hash(self.payload) != self.payload_hash:
            raise ValueError("payload_hash does not match proposal payload")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.supersedes_proposal_id == self.id:
            raise ValueError("proposal cannot supersede itself")


@dataclass(frozen=True, slots=True)
class ProposalReviewDecision:
    id: UUID
    proposal_id: UUID
    decision: ProposalReviewDecisionKind
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None = None
    reason_code: str | None = None
    policy_version: str | None = None
    risk_policy_version: str | None = None

    def __post_init__(self) -> None:
        require_text(self.reviewer_ref, "reviewer_ref")


@dataclass(frozen=True, slots=True)
class ProposalMaterialization:
    id: UUID
    proposal_id: UUID
    review_decision_id: UUID
    target_kind: str
    target_id: UUID
    materialized_at: datetime

    def __post_init__(self) -> None:
        require_text(self.target_kind, "target_kind")


@dataclass(frozen=True, slots=True)
class StageProcessorResult:
    proposals: tuple[ProposalDraft, ...] = field(default_factory=tuple)
    output_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def output_hash(self) -> str:
        normalized = {
            "proposals": [
                {
                    "kind": item.proposal_kind,
                    "schema": item.payload_schema_ref,
                    "schema_version": item.payload_schema_version,
                    "payload": item.payload,
                }
                for item in self.proposals
            ],
            "metadata": self.output_metadata,
        }
        return stable_payload_hash(normalized)

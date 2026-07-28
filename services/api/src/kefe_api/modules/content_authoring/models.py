from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ContentLifecycle(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True, slots=True)
class AuthoringQuestion:
    id: UUID
    stable_code: str
    prompt: str
    response_type: str
    response_schema: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    is_required: bool = True
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class AuthoringIssue:
    id: UUID
    code: str
    title: str
    questions: tuple[AuthoringQuestion, ...]
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class AuthoringContextBlock:
    id: UUID
    title: str
    body: str
    disclosure_level: str
    claim_status: str
    source_ids: tuple[UUID, ...] = ()
    sort_order: int = 0
    block_type: str = "CONTEXT"


@dataclass(frozen=True, slots=True)
class AuthoringSourceReference:
    id: UUID
    source_kind: str
    locator: str
    title: str
    publisher: str = ""
    published_at: datetime | None = None
    claim_status: str | None = None
    verified: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedFlowStep:
    code: str
    primitive_code: str
    capability_codes: tuple[str, ...] = ()
    next_step_codes: tuple[str, ...] = ()
    payload_schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedFlowDefinition:
    template_code: str
    template_version_no: int
    entry_step_code: str
    steps: tuple[ResolvedFlowStep, ...]


@dataclass(frozen=True, slots=True)
class PublicationConfigurationResolution:
    content_configuration_id: UUID
    content_configuration_version_no: int
    resolved_flow: ResolvedFlowDefinition


@dataclass(frozen=True, slots=True)
class CaseIdentity:
    id: UUID
    slug: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class AuthoringCaseVersion:
    id: UUID
    case_id: UUID
    version_no: int
    state: ContentLifecycle
    title: str
    summary: str
    base_format_code: str
    primary_domain_code: str
    content_risk: str
    issues: tuple[AuthoringIssue, ...]
    context_blocks: tuple[AuthoringContextBlock, ...] = ()
    sources: tuple[AuthoringSourceReference, ...] = ()
    modifiers: tuple[str, ...] = ()
    is_fact_bearing: bool = False
    is_real_event: bool = False
    required_review_modes: tuple[str, ...] = ()
    completed_review_modes: tuple[str, ...] = ()
    flow_template_code: str = "STANDARD_COMMIT_REVEAL"
    flow_template_version_no: int = 1
    content_configuration_id: UUID | None = None
    content_configuration_version_no: int | None = None
    resolved_flow: ResolvedFlowDefinition | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None

    @property
    def active_questions(self) -> tuple[AuthoringQuestion, ...]:
        return tuple(
            question
            for issue in self.issues
            for question in issue.questions
            if question.is_active
        )

    def with_state(
        self,
        state: ContentLifecycle,
        *,
        published_at: datetime | None = None,
    ) -> AuthoringCaseVersion:
        return replace(
            self,
            state=state,
            published_at=published_at if published_at is not None else self.published_at,
        )


@dataclass(frozen=True, slots=True)
class LifecycleAuditEntry:
    audit_id: UUID
    case_id: UUID
    case_version_id: UUID
    actor_ref: str
    command: str
    previous_state: ContentLifecycle | None
    new_state: ContentLifecycle
    rationale: str | None
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        version: AuthoringCaseVersion,
        actor_ref: str,
        command: str,
        previous_state: ContentLifecycle | None,
        new_state: ContentLifecycle,
        rationale: str | None = None,
        occurred_at: datetime | None = None,
    ) -> LifecycleAuditEntry:
        return cls(
            audit_id=uuid4(),
            case_id=version.case_id,
            case_version_id=version.id,
            actor_ref=actor_ref,
            command=command,
            previous_state=previous_state,
            new_state=new_state,
            rationale=rationale,
            occurred_at=occurred_at or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class PublicationValidationFailure:
    code: str
    detail: str
    path: str | None = None

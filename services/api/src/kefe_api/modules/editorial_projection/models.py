from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from typing import Any
from uuid import UUID


def stable_payload_hash(payload: dict[str, Any]) -> str:
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ReviewedProposal:
    id: UUID
    proposal_kind: str
    payload_schema_ref: str
    payload_schema_version: str
    payload: dict[str, Any]
    payload_hash: str
    review_decision_id: UUID
    review_decision: str
    dependency_ids: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        if not self.proposal_kind.strip():
            raise ValueError("proposal_kind must not be blank")
        if not self.payload_schema_ref.strip():
            raise ValueError("payload_schema_ref must not be blank")
        if not self.payload_schema_version.strip():
            raise ValueError("payload_schema_version must not be blank")
        if stable_payload_hash(self.payload) != self.payload_hash:
            raise ValueError("payload_hash does not match payload")


@dataclass(frozen=True, slots=True)
class ReviewedProposalBundle:
    candidate: ReviewedProposal
    dependencies: tuple[ReviewedProposal, ...] = ()

    def dependency_map(self) -> dict[UUID, ReviewedProposal]:
        return {item.id: item for item in self.dependencies}


@dataclass(frozen=True, slots=True)
class EditorialProjectionProfile:
    profile_code: str
    profile_version: int
    candidate_schema_ref: str
    candidate_schema_version: str
    required_dependency_kinds: frozenset[str] = field(default_factory=frozenset)
    allow_candidate_flow_selection: bool = True
    allow_command_flow_selection: bool = True

    def __post_init__(self) -> None:
        if not self.profile_code.strip():
            raise ValueError("profile_code must not be blank")
        if self.profile_version < 1:
            raise ValueError("profile_version must be >= 1")


@dataclass(frozen=True, slots=True)
class EditorialProjectionCommand:
    candidate_proposal_id: UUID
    proposal_review_decision_id: UUID
    profile_code: str
    profile_version: int
    idempotency_key: str
    requested_by_admin_ref: str
    explicit_flow_template_code: str | None = None
    explicit_flow_template_version: int | None = None

    def __post_init__(self) -> None:
        if not self.profile_code.strip():
            raise ValueError("profile_code must not be blank")
        if self.profile_version < 1:
            raise ValueError("profile_version must be >= 1")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be blank")
        if not self.requested_by_admin_ref.strip():
            raise ValueError("requested_by_admin_ref must not be blank")
        if (self.explicit_flow_template_code is None) != (
            self.explicit_flow_template_version is None
        ):
            raise ValueError("explicit Flow code and version must be provided together")
        if (
            self.explicit_flow_template_version is not None
            and self.explicit_flow_template_version < 1
        ):
            raise ValueError("explicit Flow version must be >= 1")


@dataclass(frozen=True, slots=True)
class EditorialProjectionRecord:
    id: UUID
    candidate_proposal_id: UUID
    proposal_review_decision_id: UUID
    profile_code: str
    profile_version: int
    idempotency_key: str
    requested_by_admin_ref: str
    input_hash: str
    authoring_case_id: UUID
    authoring_case_version_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class EditorialProjectionResult:
    record: EditorialProjectionRecord
    replayed: bool

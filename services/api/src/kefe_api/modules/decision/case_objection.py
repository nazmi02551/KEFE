from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ObjectionCategory(StrEnum):
    EDITORIAL_BIAS_FRAMING = "EDITORIAL_BIAS_FRAMING"
    FACTUAL_INACCURACY = "FACTUAL_INACCURACY"
    EXCLUDED_STAKEHOLDER = "EXCLUDED_STAKEHOLDER"
    AMBIGUOUS_OPTIONS = "AMBIGUOUS_OPTIONS"
    DEPRECIATED_CONTEXT = "DEPRECIATED_CONTEXT"


class ObjectionStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED_CORRECTION_FILED = "ACCEPTED_CORRECTION_FILED"
    REJECTED_WITH_REASON = "REJECTED_WITH_REASON"


@dataclass(frozen=True, slots=True)
class CaseObjectionItem:
    objection_id: UUID
    case_version_id: UUID
    reason_category: ObjectionCategory
    statement: str
    status: ObjectionStatus
    created_at: datetime
    supporting_evidence_url: str | None = None
    resolution_note: str | None = None


class CaseObjectionService:
    def __init__(self) -> None:
        self._objections: dict[UUID, CaseObjectionItem] = {}

    def submit_objection(
        self,
        *,
        case_version_id: UUID,
        reason_category: ObjectionCategory,
        statement: str,
        supporting_evidence_url: str | None = None,
    ) -> CaseObjectionItem:
        cleaned_statement = statement.strip()
        if len(cleaned_statement) < 20:
            raise ValueError("statement must have at least 20 characters for actionable deliberation")

        objection_id = uuid4()
        item = CaseObjectionItem(
            objection_id=objection_id,
            case_version_id=case_version_id,
            reason_category=reason_category,
            statement=cleaned_statement,
            supporting_evidence_url=supporting_evidence_url,
            status=ObjectionStatus.SUBMITTED,
            created_at=datetime.now(UTC),
        )

        self._objections[objection_id] = item
        return item

    def resolve_objection(
        self,
        *,
        objection_id: UUID,
        new_status: ObjectionStatus,
        resolution_note: str,
    ) -> CaseObjectionItem:
        existing = self._objections.get(objection_id)
        if not existing:
            raise KeyError(f"objection {objection_id} not found")

        resolved = CaseObjectionItem(
            objection_id=existing.objection_id,
            case_version_id=existing.case_version_id,
            reason_category=existing.reason_category,
            statement=existing.statement,
            supporting_evidence_url=existing.supporting_evidence_url,
            status=new_status,
            created_at=existing.created_at,
            resolution_note=resolution_note.strip(),
        )

        self._objections[objection_id] = resolved
        return resolved

    def get_objections_for_case(self, case_version_id: UUID) -> list[CaseObjectionItem]:
        return [
            item for item in self._objections.values()
            if item.case_version_id == case_version_id
        ]

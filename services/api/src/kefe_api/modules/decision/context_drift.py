from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ContextDriftType(StrEnum):
    LEGAL_REFORM = "LEGAL_REFORM"
    FACTUAL_UPDATE = "FACTUAL_UPDATE"
    ASSUMPTION_CHANGED = "ASSUMPTION_CHANGED"
    SUPERSEDED_BASELINE = "SUPERSEDED_BASELINE"


class DriftRecommendedAction(StrEnum):
    CONTINUE_WITH_AWARENESS = "CONTINUE_WITH_AWARENESS"
    REVIEW_AMENDMENT = "REVIEW_AMENDMENT"
    CASE_SUPERSEDED = "CASE_SUPERSEDED"


@dataclass(frozen=True, slots=True)
class ContextDriftNotice:
    notice_id: UUID
    case_version_id: UUID
    drift_type: ContextDriftType
    effective_date: datetime
    summary: str
    recommended_action: DriftRecommendedAction
    created_at: datetime
    source_reference_url: str | None = None


class ContextDriftService:
    def __init__(self) -> None:
        self._notices_by_case: dict[UUID, list[ContextDriftNotice]] = {}

    def publish_notice(
        self,
        *,
        case_version_id: UUID,
        drift_type: ContextDriftType,
        effective_date: datetime,
        summary: str,
        recommended_action: DriftRecommendedAction,
        source_reference_url: str | None = None,
    ) -> ContextDriftNotice:
        cleaned_summary = summary.strip()
        if len(cleaned_summary) < 10:
            raise ValueError("summary must have at least 10 characters")

        notice = ContextDriftNotice(
            notice_id=uuid4(),
            case_version_id=case_version_id,
            drift_type=drift_type,
            effective_date=effective_date,
            summary=cleaned_summary,
            recommended_action=recommended_action,
            source_reference_url=source_reference_url,
            created_at=datetime.now(UTC),
        )

        self._notices_by_case.setdefault(case_version_id, []).append(notice)
        return notice

    def get_notices_for_case(self, case_version_id: UUID) -> list[ContextDriftNotice]:
        return list(self._notices_by_case.get(case_version_id, []))

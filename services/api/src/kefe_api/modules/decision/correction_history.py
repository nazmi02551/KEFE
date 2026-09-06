from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class CorrectionType(StrEnum):
    FACTUAL_UPDATE = "FACTUAL_UPDATE"
    CLARIFICATION = "CLARIFICATION"
    SOURCE_EXPANSION = "SOURCE_EXPANSION"
    TYPO_FIX = "TYPO_FIX"
    LEGAL_STATUS_UPDATE = "LEGAL_STATUS_UPDATE"


class CorrectionSeverity(StrEnum):
    MINOR = "MINOR"
    MATERIAL = "MATERIAL"
    SUBSTANTIAL = "SUBSTANTIAL"


@dataclass(frozen=True, slots=True)
class CaseCorrectionItem:
    correction_id: UUID
    case_version_id: UUID
    correction_type: CorrectionType
    severity: CorrectionSeverity
    summary: str
    editorial_rationale: str
    timestamp: datetime
    previous_text: str | None = None
    corrected_text: str | None = None


@dataclass(frozen=True, slots=True)
class CaseCorrectionHistoryResult:
    case_version_id: UUID
    corrections: tuple[CaseCorrectionItem, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_version_id": str(self.case_version_id),
            "corrections": [
                {
                    "correction_id": str(c.correction_id),
                    "case_version_id": str(c.case_version_id),
                    "correction_type": c.correction_type.value,
                    "severity": c.severity.value,
                    "summary": c.summary,
                    "editorial_rationale": c.editorial_rationale,
                    "timestamp": c.timestamp.isoformat(),
                    "previous_text": c.previous_text,
                    "corrected_text": c.corrected_text,
                }
                for c in self.corrections
            ],
        }


class CaseCorrectionHistoryService:
    def __init__(self) -> None:
        self._history_by_case: dict[UUID, list[CaseCorrectionItem]] = {}

    def log_correction(
        self,
        *,
        case_version_id: UUID,
        correction_type: CorrectionType,
        severity: CorrectionSeverity,
        summary: str,
        editorial_rationale: str,
        previous_text: str | None = None,
        corrected_text: str | None = None,
        timestamp: datetime | None = None,
    ) -> CaseCorrectionItem:
        cl_sum = summary.strip()
        cl_rat = editorial_rationale.strip()

        if len(cl_sum) < 5:
            raise ValueError("summary must have at least 5 characters")
        if len(cl_rat) < 10:
            raise ValueError("editorial_rationale must have at least 10 characters")

        item = CaseCorrectionItem(
            correction_id=uuid4(),
            case_version_id=case_version_id,
            correction_type=correction_type,
            severity=severity,
            summary=cl_sum,
            editorial_rationale=cl_rat,
            previous_text=previous_text,
            corrected_text=corrected_text,
            timestamp=timestamp or datetime.now(UTC),
        )

        self._history_by_case.setdefault(case_version_id, []).append(item)
        return item

    def get_history(self, case_version_id: UUID) -> CaseCorrectionHistoryResult:
        records = self._history_by_case.get(case_version_id, [])
        sorted_records = sorted(records, key=lambda r: r.timestamp, reverse=True)
        return CaseCorrectionHistoryResult(
            case_version_id=case_version_id,
            corrections=tuple(sorted_records),
        )

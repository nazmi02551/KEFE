from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class EvidenceCategory(StrEnum):
    ACADEMIC_PEER_REVIEWED = "ACADEMIC_PEER_REVIEWED"
    OFFICIAL_GOVERNMENT_STAT = "OFFICIAL_GOVERNMENT_STAT"
    INVESTIGATIVE_JOURNALISM = "INVESTIGATIVE_JOURNALISM"
    INSTITUTIONAL_REPORT = "INSTITUTIONAL_REPORT"


class EvidenceVerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    COMMUNITY_VERIFIED = "COMMUNITY_VERIFIED"
    EXPERT_AUDITED = "EXPERT_AUDITED"


@dataclass(frozen=True, slots=True)
class StructuredEvidenceItem:
    evidence_id: UUID
    case_version_id: UUID
    category: EvidenceCategory
    title: str
    publisher: str
    verification_status: EvidenceVerificationStatus
    created_at: datetime
    reason_id: UUID | None = None
    source_url: str | None = None
    doi_or_doc_ref: str | None = None


class EvidenceBuilderService:
    def __init__(self) -> None:
        self._evidence_by_case: dict[UUID, list[StructuredEvidenceItem]] = {}

    def attach_evidence(
        self,
        *,
        case_version_id: UUID,
        category: EvidenceCategory,
        title: str,
        publisher: str,
        reason_id: UUID | None = None,
        source_url: str | None = None,
        doi_or_doc_ref: str | None = None,
        verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.UNVERIFIED,
    ) -> StructuredEvidenceItem:
        cleaned_title = title.strip()
        if len(cleaned_title) < 5:
            raise ValueError("title must have at least 5 characters")

        item = StructuredEvidenceItem(
            evidence_id=uuid4(),
            case_version_id=case_version_id,
            reason_id=reason_id,
            category=category,
            title=cleaned_title,
            publisher=publisher.strip(),
            source_url=source_url,
            doi_or_doc_ref=doi_or_doc_ref,
            verification_status=verification_status,
            created_at=datetime.now(UTC),
        )

        self._evidence_by_case.setdefault(case_version_id, []).append(item)
        return item

    def get_evidence_for_case(self, case_version_id: UUID) -> list[StructuredEvidenceItem]:
        return list(self._evidence_by_case.get(case_version_id, []))

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class LensPillarType(StrEnum):
    LEGAL_FRAMEWORK = "LEGAL_FRAMEWORK"
    HISTORICAL_CONTEXT = "HISTORICAL_CONTEXT"
    SCIENTIFIC_DATA = "SCIENTIFIC_DATA"
    COMPARATIVE_PRACTICE = "COMPARATIVE_PRACTICE"


@dataclass(frozen=True, slots=True)
class ContextLensPillar:
    pillar_type: LensPillarType
    title: str
    content: str
    source_citation: str
    source_url: str | None = None


@dataclass(frozen=True, slots=True)
class ContextLensResult:
    case_version_id: UUID
    pillars: tuple[ContextLensPillar, ...]


class ContextLensService:
    def __init__(self) -> None:
        self._lenses_by_case: dict[UUID, list[ContextLensPillar]] = {}

    def add_pillar(
        self,
        *,
        case_version_id: UUID,
        pillar_type: LensPillarType,
        title: str,
        content: str,
        source_citation: str,
        source_url: str | None = None,
    ) -> ContextLensPillar:
        cleaned_content = content.strip()
        if len(cleaned_content) < 20:
            raise ValueError("content must have at least 20 characters for contextual depth")

        pillar = ContextLensPillar(
            pillar_type=pillar_type,
            title=title.strip(),
            content=cleaned_content,
            source_citation=source_citation.strip(),
            source_url=source_url,
        )

        self._lenses_by_case.setdefault(case_version_id, []).append(pillar)
        return pillar

    def get_lens_for_case(self, case_version_id: UUID) -> ContextLensResult:
        pillars = self._lenses_by_case.get(case_version_id, [])
        return ContextLensResult(
            case_version_id=case_version_id,
            pillars=tuple(pillars),
        )

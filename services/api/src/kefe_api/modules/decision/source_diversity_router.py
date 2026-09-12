"""Source Diversity Indicator Router (CAP-071, KEFE-SOURCE-DIVERSITY-001).

Implements source plurality taxonomy evaluation and diversity level calculation.
Invariants:
- Plurality taxonomy enforced across academic, official, civic, journalistic, and industry sources.
- Non-monopolistic sources prevented through diversity entropy classification.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from kefe_api.modules.decision.source_diversity import (
    DiversityLevel,
    SourceDiversityCalculator,
    SourcePluralityCategory,
)

router = APIRouter(prefix="/v1/cases", tags=["source-diversity"])

# In-memory storage for evaluated source diversity per case_version_id
_CASE_SOURCE_REGISTRY: dict[UUID, list[SourcePluralityCategory]] = {}


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0.0, le=100.0)


class SourceDiversityResponse(BaseModel):
    case_version_id: str
    total_sources: int = Field(..., ge=1)
    diversity_level: str
    category_breakdown: list[CategoryBreakdownItem]


class EvaluateDiversityRequest(BaseModel):
    source_categories: list[str] = Field(..., min_length=1)


@router.get("/{case_version_id}/source-diversity", response_model=SourceDiversityResponse)
def get_source_diversity(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve source diversity evaluation for a case version."""
    categories = _CASE_SOURCE_REGISTRY.get(case_version_id)
    if not categories:
        # Provide balanced default plurality if not explicitly seeded
        categories = [
            SourcePluralityCategory.ACADEMIC_SCIENTIFIC,
            SourcePluralityCategory.OFFICIAL_GOVERNMENT,
            SourcePluralityCategory.CIVIC_INDEPENDENT,
            SourcePluralityCategory.MAINSTREAM_JOURNALISM,
        ]
        _CASE_SOURCE_REGISTRY[case_version_id] = categories

    result = SourceDiversityCalculator.calculate(case_version_id, categories)
    return result.to_dict()


@router.post("/{case_version_id}/source-diversity/evaluate", response_model=SourceDiversityResponse)
def evaluate_source_diversity(
    case_version_id: UUID,
    payload: EvaluateDiversityRequest,
) -> dict[str, Any]:
    """Evaluate and store source diversity breakdown for a case version."""
    parsed_categories: list[SourcePluralityCategory] = []
    for cat_str in payload.source_categories:
        try:
            parsed_categories.append(SourcePluralityCategory(cat_str))
        except ValueError:
            valid_cats = [c.value for c in SourcePluralityCategory]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{cat_str}'. Must be one of: {valid_cats}",
            )

    result = SourceDiversityCalculator.calculate(case_version_id, parsed_categories)
    _CASE_SOURCE_REGISTRY[case_version_id] = parsed_categories
    return result.to_dict()

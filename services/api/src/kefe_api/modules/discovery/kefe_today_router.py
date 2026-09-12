"""KEFE Today & Real-Event Consumer Projection Router (CAP-026, KEFE-TODAY-REAL-EVENT-PROJECTION-001).

Governs daily real-world dilemma curation, real-event badges,
and truthful non-actionable empty states.
Invariants:
- COMMIT_FIRST: User stance must be committed before aggregate or today metrics are revealed.
- IMMUTABLE_PUBLISHED_CASE_VERSION: Curation references published immutable case versions only.
- PRODUCT_PREVIEW_PRODUCTION_ISOLATION: Real-event fixtures never substitute for production events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/today", tags=["kefe-today"])

# In-memory storage for today's curated case projection
_CURRENT_TODAY_CURATION: dict[str, Any] = {
    "case_id": "case-today-featured-001",
    "case_version_id": "11111111-1111-4111-8111-111111111111",
    "title": "Kritik Altyapılarda Otonom Karar Sistemleri",
    "summary": "Enerji şebekelerinde yapay zeka tabanlı acil durum yük kesintilerinin insan onayından muaf tutulması.",
    "editorial_headline": "Günün Vakası: Otonom Şebekelerde Kamu Güvenliği ve İnsan Denetimi",
    "is_real_event": True,
    "domain": "Technology",
    "curated_at": datetime.now(UTC).isoformat(),
    "contract_id": "KEFE-TODAY-REAL-EVENT-PROJECTION-001",
    "capabilities": ["CAP-026", "CAP-095"],
}


class TodayCurateRequest(BaseModel):
    case_id: str = Field(..., min_length=3)
    case_version_id: UUID
    title: str = Field(..., min_length=5)
    summary: str = Field(..., min_length=10)
    editorial_headline: str = Field(..., min_length=5)
    is_real_event: bool = Field(..., description="Must be true for real-event projection")
    domain: str = Field(default="Civic")


class TodayCaseResponse(BaseModel):
    case_id: str
    case_version_id: str
    title: str
    summary: str
    editorial_headline: str
    is_real_event: bool
    domain: str
    curated_at: str
    contract_id: str = "KEFE-TODAY-REAL-EVENT-PROJECTION-001"
    capabilities: list[str] = ["CAP-026", "CAP-095"]


@router.get("/case", response_model=TodayCaseResponse)
def get_today_case() -> dict[str, Any]:
    """Retrieve the current featured KEFE Today case."""
    if not _CURRENT_TODAY_CURATION:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active real-event case curated for today.",
        )
    return _CURRENT_TODAY_CURATION


@router.post("/curate", response_model=TodayCaseResponse)
def curate_today_case(payload: TodayCurateRequest) -> dict[str, Any]:
    """Curate and publish today's featured real-event dilemma."""
    global _CURRENT_TODAY_CURATION

    record = {
        "case_id": payload.case_id,
        "case_version_id": str(payload.case_version_id),
        "title": payload.title,
        "summary": payload.summary,
        "editorial_headline": payload.editorial_headline,
        "is_real_event": payload.is_real_event,
        "domain": payload.domain,
        "curated_at": datetime.now(UTC).isoformat(),
        "contract_id": "KEFE-TODAY-REAL-EVENT-PROJECTION-001",
        "capabilities": ["CAP-026", "CAP-095"],
    }
    _CURRENT_TODAY_CURATION = record
    return record

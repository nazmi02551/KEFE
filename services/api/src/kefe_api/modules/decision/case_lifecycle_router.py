from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

case_lifecycle_router = APIRouter(prefix="/v1/cases", tags=["Case Lifecycle & Saved Follow Updates"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseLifecycleStatusResponse(StrictModel):
    case_id: str
    current_case_version_id: str
    version_number: int
    is_published: bool
    has_institutional_response: bool
    update_summary: str
    last_updated_at: datetime


class SavedCaseQueryItem(StrictModel):
    case_id: str = Field(..., min_length=2, max_length=128)
    saved_version_id: str = Field(..., min_length=2, max_length=128)


class ReconcileSavedCasesRequest(StrictModel):
    saved_cases: list[SavedCaseQueryItem] = Field(..., min_length=1, max_length=100)


class ReconciledCaseResult(StrictModel):
    case_id: str
    saved_version_id: str
    current_case_version_id: str
    has_update: bool
    change_type: Literal["NONE", "VERSION_SHIFT", "INSTITUTION_RESPONSE"]
    notification_label_tr: str
    notification_label_en: str


class ReconcileSavedCasesResponse(StrictModel):
    total_checked: int
    updated_count: int
    results: list[ReconciledCaseResult]
    reconciled_at: datetime


# Seed case repository mapping
_SEED_CASES: dict[str, dict] = {
    "case_ai_001": {
        "current_case_version_id": "v2_ai_governance",
        "version_number": 2,
        "is_published": True,
        "has_institutional_response": True,
        "update_summary": "BTK resmi inceleme yanıtı yayımlandı ve 2. versiyona güncellendi.",
        "last_updated_at": datetime(2026, 9, 12, 10, 0, 0, tzinfo=UTC),
    },
    "case_edu_002": {
        "current_case_version_id": "v1_curriculum_standard",
        "version_number": 1,
        "is_published": True,
        "has_institutional_response": False,
        "update_summary": "İlk yayınlanmış kararlı sürüm.",
        "last_updated_at": datetime(2026, 9, 10, 14, 0, 0, tzinfo=UTC),
    },
    "case_urban_003": {
        "current_case_version_id": "v3_urban_density",
        "version_number": 3,
        "is_published": True,
        "has_institutional_response": True,
        "update_summary": "Çevre ve Şehircilik Bakanlığı taahhüt planı eklendi.",
        "last_updated_at": datetime(2026, 9, 12, 16, 0, 0, tzinfo=UTC),
    },
}


@case_lifecycle_router.get(
    "/{case_id}/lifecycle",
    response_model=CaseLifecycleStatusResponse,
    summary="Get case lifecycle and published version status (CAP-079)",
)
def get_case_lifecycle(case_id: str) -> CaseLifecycleStatusResponse:
    info = _SEED_CASES.get(case_id)
    if not info:
        # Fallback dynamic resolution
        return CaseLifecycleStatusResponse(
            case_id=case_id,
            current_case_version_id=f"{case_id}_v1",
            version_number=1,
            is_published=True,
            has_institutional_response=False,
            update_summary="Güncel vaka sürümü.",
            last_updated_at=datetime.now(UTC),
        )

    return CaseLifecycleStatusResponse(
        case_id=case_id,
        current_case_version_id=info["current_case_version_id"],
        version_number=info["version_number"],
        is_published=info["is_published"],
        has_institutional_response=info["has_institutional_response"],
        update_summary=info["update_summary"],
        last_updated_at=info["last_updated_at"],
    )


@case_lifecycle_router.post(
    "/reconcile-saved",
    response_model=ReconcileSavedCasesResponse,
    summary="Reconcile saved cases and detect version shifts or institutional responses (CAP-079)",
)
def reconcile_saved_cases(
    request: ReconcileSavedCasesRequest,
) -> ReconcileSavedCasesResponse:
    results: list[ReconciledCaseResult] = []
    updated_count = 0

    for item in request.saved_cases:
        info = _SEED_CASES.get(item.case_id)
        current_v = info["current_case_version_id"] if info else item.saved_version_id
        has_resp = info["has_institutional_response"] if info else False

        has_version_shift = current_v != item.saved_version_id
        if has_version_shift:
            change = "VERSION_SHIFT"
            tr = "Vaka yeni bir sürüme güncellendi"
            en = "Case updated to a newer version"
            updated = True
        elif has_resp:
            change = "INSTITUTION_RESPONSE"
            tr = "Kurumsal resmi yanıt eklendi"
            en = "Verified institutional response added"
            updated = True
        else:
            change = "NONE"
            tr = "Değişiklik yok"
            en = "No updates"
            updated = False

        if updated:
            updated_count += 1

        results.append(
            ReconciledCaseResult(
                case_id=item.case_id,
                saved_version_id=item.saved_version_id,
                current_case_version_id=current_v,
                has_update=updated,
                change_type=change,
                notification_label_tr=tr,
                notification_label_en=en,
            )
        )

    return ReconcileSavedCasesResponse(
        total_checked=len(request.saved_cases),
        updated_count=updated_count,
        results=results,
        reconciled_at=datetime.now(UTC),
    )

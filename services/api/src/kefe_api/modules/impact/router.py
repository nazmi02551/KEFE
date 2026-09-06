from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus
from kefe_api.modules.impact.action_service import ActionFollowThroughService
from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)
from kefe_api.modules.impact.service import InstitutionResponseService

impact_router = APIRouter(prefix="/v1/impact", tags=["Impact"])

_DEFAULT_SERVICE = InstitutionResponseService()
_DEFAULT_ACTION_SERVICE = ActionFollowThroughService()

# Seed default verified institution responses for preview/production cases
_DEFAULT_SERVICE.publish_response(
    case_version_id=UUID("22222222-2222-4222-8222-222222222222"),
    institution_name="Ulaştırma ve Altyapı Denetleme Kurulu",
    authority_role="Halkla İlişkiler ve Yolcu Hakları Dairesi",
    response_type=InstitutionResponseType.POLICY_CHANGE,
    statement="Topluluk müzakereleri ve yüksek uzlaşı verileri dikkate alınarak öncelikli yolcu kontenjanı genelgeye eklenmiştir.",
    verification_status=AuthorityVerificationStatus.VERIFIED,
)
_DEFAULT_SERVICE.publish_response(
    case_version_id=UUID("22222222-2222-4222-8222-222222222223"),
    institution_name="Kişisel Verileri Koruma Kurumu (KVKK)",
    authority_role="Veri Güvenliği ve Yapay Zekâ İzleme Masası",
    response_type=InstitutionResponseType.COMMITMENT,
    statement="Model eğitimi amaçlı veri toplama süreçlerine ilişkin şeffaflık kılavuzu taslağı kamuoyu görüşüne açılmıştır.",
    verification_status=AuthorityVerificationStatus.VERIFIED,
)

# Seed default action follow-throughs
_DEFAULT_ACTION_SERVICE.propose_action(
    case_version_id=UUID("22222222-2222-4222-8222-222222222222"),
    title="Toplu Taşıma Gece Seferleri ve Öncelikli Koltuk Yönetmeliği",
    description="Belediye meclisine resmi dilekçe verilmesi ve tarife komisyonu toplantısının izlenmesi.",
    target_completion_date=datetime(2026, 10, 15, tzinfo=UTC),
)
_action_list = _DEFAULT_ACTION_SERVICE.list_actions(
    UUID("22222222-2222-4222-8222-222222222222")
)
if _action_list:
    _DEFAULT_ACTION_SERVICE.update_progress(
        case_version_id=UUID("22222222-2222-4222-8222-222222222222"),
        action_id=_action_list[0].action_id,
        progress_percentage=65,
        status=ActionStatus.IN_PROGRESS,
        evidence_summary="Dilekçe kabul edildi, belediye meclisi gündemine alındı.",
        evidence_url="https://belediye.gov.tr/kararlar/2026-44",
    )


def get_institution_response_service() -> InstitutionResponseService:
    return _DEFAULT_SERVICE


def get_action_service() -> ActionFollowThroughService:
    return _DEFAULT_ACTION_SERVICE


class InstitutionResponseOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    response_id: UUID
    case_version_id: UUID
    institution_name: str = Field(min_length=2, max_length=150)
    authority_role: str = Field(min_length=2, max_length=100)
    verification_status: str
    response_type: str
    statement: str = Field(min_length=10, max_length=2000)
    published_at: datetime
    milestone_date: datetime | None = None


class ActionMilestoneOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: UUID
    case_version_id: UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    status: str
    progress_percentage: int = Field(ge=0, le=100)
    created_at: datetime
    institution_response_id: UUID | None = None
    target_completion_date: datetime | None = None
    evidence_summary: str | None = None
    evidence_url: str | None = None


class ProposeActionIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_version_id: UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    institution_response_id: UUID | None = None
    target_completion_date: datetime | None = None


class UpdateProgressIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_version_id: UUID
    progress_percentage: int = Field(ge=0, le=100)
    status: str
    evidence_summary: str | None = None
    evidence_url: str | None = None


@impact_router.get(
    "/institution-responses",
    response_model=list[InstitutionResponseOut],
)
def list_institution_responses(
    case_version_id: Annotated[UUID | None, Query()] = None,
    service: InstitutionResponseService = Depends(
        get_institution_response_service
    ),
) -> list[InstitutionResponseOut]:
    if case_version_id:
        responses = service.list_verified_responses(case_version_id)
    else:
        responses = []
        for case_id in service._responses_by_case:
            responses.extend(service.list_verified_responses(case_id))

    return [
        InstitutionResponseOut(
            response_id=r.response_id,
            case_version_id=r.case_version_id,
            institution_name=r.institution_name,
            authority_role=r.authority_role,
            verification_status=r.verification_status.value,
            response_type=r.response_type.value,
            statement=r.statement,
            published_at=r.published_at,
            milestone_date=r.milestone_date,
        )
        for r in responses
    ]


@impact_router.get(
    "/actions",
    response_model=list[ActionMilestoneOut],
)
def list_actions(
    case_version_id: Annotated[UUID | None, Query()] = None,
    service: ActionFollowThroughService = Depends(get_action_service),
) -> list[ActionMilestoneOut]:
    if case_version_id:
        actions = service.list_actions(case_version_id)
    else:
        actions = []
        for case_id in service._actions_by_case:
            actions.extend(service.list_actions(case_id))

    return [
        ActionMilestoneOut(
            action_id=a.action_id,
            case_version_id=a.case_version_id,
            title=a.title,
            description=a.description,
            status=a.status.value,
            progress_percentage=a.progress_percentage,
            created_at=a.created_at,
            institution_response_id=a.institution_response_id,
            target_completion_date=a.target_completion_date,
            evidence_summary=a.evidence_summary,
            evidence_url=a.evidence_url,
        )
        for a in actions
    ]


@impact_router.post(
    "/actions",
    response_model=ActionMilestoneOut,
    status_code=201,
)
def propose_action(
    payload: ProposeActionIn,
    service: ActionFollowThroughService = Depends(get_action_service),
) -> ActionMilestoneOut:
    try:
        a = service.propose_action(
            case_version_id=payload.case_version_id,
            title=payload.title,
            description=payload.description,
            institution_response_id=payload.institution_response_id,
            target_completion_date=payload.target_completion_date,
        )
        return ActionMilestoneOut(
            action_id=a.action_id,
            case_version_id=a.case_version_id,
            title=a.title,
            description=a.description,
            status=a.status.value,
            progress_percentage=a.progress_percentage,
            created_at=a.created_at,
            institution_response_id=a.institution_response_id,
            target_completion_date=a.target_completion_date,
            evidence_summary=a.evidence_summary,
            evidence_url=a.evidence_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@impact_router.patch(
    "/actions/{action_id}/progress",
    response_model=ActionMilestoneOut,
)
def update_action_progress(
    action_id: UUID,
    payload: UpdateProgressIn,
    service: ActionFollowThroughService = Depends(get_action_service),
) -> ActionMilestoneOut:
    try:
        status_enum = ActionStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}",
        )

    try:
        a = service.update_progress(
            case_version_id=payload.case_version_id,
            action_id=action_id,
            progress_percentage=payload.progress_percentage,
            status=status_enum,
            evidence_summary=payload.evidence_summary,
            evidence_url=payload.evidence_url,
        )
        return ActionMilestoneOut(
            action_id=a.action_id,
            case_version_id=a.case_version_id,
            title=a.title,
            description=a.description,
            status=a.status.value,
            progress_percentage=a.progress_percentage,
            created_at=a.created_at,
            institution_response_id=a.institution_response_id,
            target_completion_date=a.target_completion_date,
            evidence_summary=a.evidence_summary,
            evidence_url=a.evidence_url,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Action not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

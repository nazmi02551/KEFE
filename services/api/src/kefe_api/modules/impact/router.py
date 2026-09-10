from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus
from kefe_api.modules.impact.models import (
    InstitutionResponse,
)
from kefe_api.modules.impact.ports import ImpactRepository

impact_router = APIRouter(prefix="/v1/impact", tags=["Impact"])


# ---------------------------------------------------------------------------
# Dependency — injects ImpactRepository from app.state
# ---------------------------------------------------------------------------

def _get_impact_repository(request: Request) -> ImpactRepository:
    repo: ImpactRepository = request.app.state.impact_repository
    return repo


ImpactRepoDep = Annotated[ImpactRepository, Depends(_get_impact_repository)]


# ---------------------------------------------------------------------------
# Response / request models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def _response_out(r: InstitutionResponse) -> InstitutionResponseOut:
    return InstitutionResponseOut(
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


def _action_out(a: ActionMilestone) -> ActionMilestoneOut:
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


# ---------------------------------------------------------------------------
# Institution Response endpoints
# ---------------------------------------------------------------------------

@impact_router.get(
    "/institution-responses",
    response_model=list[InstitutionResponseOut],
)
def list_institution_responses(
    repo: ImpactRepoDep,
    case_version_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[InstitutionResponseOut]:
    """List verified institution responses, optionally filtered by case."""
    if case_version_id is not None:
        responses = repo.list_verified_responses(case_version_id)
        return [_response_out(r) for r in responses[offset : offset + limit]]
    responses = repo.list_all_responses(limit=limit, offset=offset)
    return [_response_out(r) for r in responses]


# ---------------------------------------------------------------------------
# Action Milestone endpoints
# ---------------------------------------------------------------------------

@impact_router.get(
    "/actions",
    response_model=list[ActionMilestoneOut],
)
def list_actions(
    repo: ImpactRepoDep,
    case_version_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ActionMilestoneOut]:
    """List action milestones, optionally filtered by case."""
    if case_version_id is not None:
        actions = repo.list_actions(case_version_id, limit=limit, offset=offset)
    else:
        actions = repo.list_all_actions(limit=limit, offset=offset)
    return [_action_out(a) for a in actions]


@impact_router.post(
    "/actions",
    response_model=ActionMilestoneOut,
    status_code=201,
)
def propose_action(
    payload: ProposeActionIn,
    repo: ImpactRepoDep,
) -> ActionMilestoneOut:
    """Propose a new action milestone linked to a case."""
    cleaned_title = payload.title.strip()
    cleaned_desc = payload.description.strip()

    if len(cleaned_title) < 3:
        raise HTTPException(status_code=400, detail="title must have at least 3 characters")
    if len(cleaned_desc) < 10:
        raise HTTPException(status_code=400, detail="description must have at least 10 characters")

    action = ActionMilestone(
        action_id=uuid4(),
        case_version_id=payload.case_version_id,
        title=cleaned_title,
        description=cleaned_desc,
        status=ActionStatus.PROPOSED,
        progress_percentage=0,
        institution_response_id=payload.institution_response_id,
        target_completion_date=payload.target_completion_date,
        created_at=datetime.now(UTC),
    )
    repo.save_action(action)
    return _action_out(action)


@impact_router.patch(
    "/actions/{action_id}/progress",
    response_model=ActionMilestoneOut,
)
def update_action_progress(
    action_id: UUID,
    payload: UpdateProgressIn,
    repo: ImpactRepoDep,
) -> ActionMilestoneOut:
    """Update the progress and status of an existing action milestone."""
    try:
        status_enum = ActionStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}. "
                   f"Valid values: {[s.value for s in ActionStatus]}",
        ) from exc

    existing = repo.get_action(action_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")

    if existing.case_version_id != payload.case_version_id:
        raise HTTPException(
            status_code=400,
            detail="case_version_id does not match the stored action",
        )

    updated = ActionMilestone(
        action_id=existing.action_id,
        case_version_id=existing.case_version_id,
        title=existing.title,
        description=existing.description,
        status=status_enum,
        progress_percentage=payload.progress_percentage,
        institution_response_id=existing.institution_response_id,
        target_completion_date=existing.target_completion_date,
        created_at=existing.created_at,
        evidence_summary=payload.evidence_summary,
        evidence_url=payload.evidence_url,
    )
    try:
        repo.update_action(updated)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found") from exc

    return _action_out(updated)
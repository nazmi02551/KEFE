from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from kefe_api.modules.consensus.models import ConsensusCardView
from kefe_api.modules.consensus.service import ConsensusService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Consensus"])


class ConsensusParticipationRequest(BaseModel):
    stance_code: str = Field(min_length=1, max_length=32)
    reason_tag_codes: list[str] = Field(default_factory=list, max_length=10)


class ConsensusParticipationResponse(BaseModel):
    stance_code: str
    reason_tag_codes: list[str]
    contribution_class: str
    participated_at: datetime


class ConsensusAggregateResponse(BaseModel):
    sample_size: int
    stance_distribution: dict[str, float]
    reason_pattern_distribution: dict[str, float]
    contribution_class: str
    methodology_version: str
    generated_at: datetime
    provenance_note: str


class ConsensusCardResponse(BaseModel):
    card_id: UUID
    card_version_id: UUID
    case_version_id: UUID
    proposition: str
    stance_codes: list[str]
    reason_tag_codes: list[str]
    max_reason_tags: int
    methodology_version: str
    participation_state: str
    contribution_class: str
    participation: ConsensusParticipationResponse | None = None
    aggregate: ConsensusAggregateResponse | None = None


class ConsensusCardsResponse(BaseModel):
    items: list[ConsensusCardResponse]


def get_service(request: Request) -> ConsensusService:
    return request.app.state.consensus_service


ConsensusServiceDep = Annotated[ConsensusService, Depends(get_service)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


def _response(view: ConsensusCardView) -> ConsensusCardResponse:
    participation = view.participation
    aggregate = view.aggregate
    return ConsensusCardResponse(
        card_id=view.card.card_id,
        card_version_id=view.card.id,
        case_version_id=view.card.case_version_id,
        proposition=view.card.proposition,
        stance_codes=list(view.card.stance_codes),
        reason_tag_codes=list(view.card.reason_tag_codes),
        max_reason_tags=view.card.max_reason_tags,
        methodology_version=view.card.methodology_version,
        participation_state=view.participation_state,
        contribution_class=(
            participation.contribution_class if participation is not None else "EXPOSED"
        ),
        participation=(
            None
            if participation is None
            else ConsensusParticipationResponse(
                stance_code=participation.stance_code,
                reason_tag_codes=list(participation.reason_tag_codes),
                contribution_class=participation.contribution_class,
                participated_at=participation.participated_at,
            )
        ),
        aggregate=(
            None
            if aggregate is None
            else ConsensusAggregateResponse(
                sample_size=aggregate.sample_size,
                stance_distribution=dict(aggregate.stance_distribution),
                reason_pattern_distribution=dict(aggregate.reason_pattern_distribution),
                contribution_class=aggregate.contribution_class,
                methodology_version=aggregate.methodology_version,
                generated_at=aggregate.generated_at,
                provenance_note=aggregate.provenance_note,
            )
        ),
    )


@router.get(
    "/weigh-sessions/{session_id}/consensus-cards",
    response_model=ConsensusCardsResponse,
)
def list_consensus_cards(
    session_id: UUID,
    principal: PrincipalDep,
    service: ConsensusServiceDep,
) -> ConsensusCardsResponse:
    return ConsensusCardsResponse(
        items=[
            _response(view)
            for view in service.list_cards(
                actor_id=principal.actor_id,
                session_id=session_id,
            )
        ]
    )


@router.post(
    "/weigh-sessions/{session_id}/consensus-cards/{card_id}/participation",
    response_model=ConsensusCardResponse,
)
def participate_in_consensus(
    session_id: UUID,
    card_id: UUID,
    body: ConsensusParticipationRequest,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDep,
    service: ConsensusServiceDep,
) -> ConsensusCardResponse:
    return _response(
        service.participate(
            actor_id=principal.actor_id,
            session_id=session_id,
            card_id=card_id,
            stance_code=body.stance_code,
            reason_tag_codes=body.reason_tag_codes,
            idempotency_key=idempotency_key,
        )
    )

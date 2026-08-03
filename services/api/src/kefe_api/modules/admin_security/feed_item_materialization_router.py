from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kefe_api.modules.admin_security.feed_item_materialization import (
    SecuredFeedItemMaterializationService,
)
from kefe_api.modules.admin_security.router import StrictModel, WritePrincipalDep

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class FeedItemMaterializationRequest(StrictModel):
    proposal_review_decision_id: UUID


class FeedItemMaterializationResponse(StrictModel):
    proposal_materialization_id: UUID
    proposal_id: UUID
    proposal_review_decision_id: UUID
    target_kind: str
    target_id: UUID
    replayed: bool


def get_feed_item_materialization(
    request: Request,
) -> SecuredFeedItemMaterializationService:
    return request.app.state.secured_feed_item_materialization_service


FeedItemMaterializationDep = Annotated[
    SecuredFeedItemMaterializationService,
    Depends(get_feed_item_materialization),
]


@router.post(
    "/feed-item-proposals/{proposal_id}/materialization",
    response_model=FeedItemMaterializationResponse,
)
def materialize_feed_item(
    proposal_id: UUID,
    body: FeedItemMaterializationRequest,
    principal: WritePrincipalDep,
    materialization: FeedItemMaterializationDep,
) -> FeedItemMaterializationResponse:
    result = materialization.materialize(
        principal,
        proposal_id=proposal_id,
        proposal_review_decision_id=body.proposal_review_decision_id,
    )
    record = result.materialization
    return FeedItemMaterializationResponse(
        proposal_materialization_id=record.id,
        proposal_id=record.proposal_id,
        proposal_review_decision_id=record.review_decision_id,
        target_kind=record.target_kind,
        target_id=record.target_id,
        replayed=result.replayed,
    )


__all__ = [
    "FeedItemMaterializationRequest",
    "FeedItemMaterializationResponse",
    "router",
]

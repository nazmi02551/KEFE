from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kefe_api.modules.admin_security.feed_item_review_router import (
    get_feed_item_review,
)
from kefe_api.modules.admin_security.router import StrictModel, WritePrincipalDep
from kefe_api.modules.admin_security.source_brief_ingestion import (
    SecuredSourceBriefIngestionService,
)
from kefe_api.modules.ingestion_orchestration.source_brief_ingestion import (
    SourceBriefStageProcessor,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class SourceBriefIngestionResponse(StrictModel):
    normalized_artifact_id: UUID
    run_id: UUID
    source_brief_proposal_id: UUID
    run_state: str
    proposal_review_state: str


def get_source_brief_ingestion(
    request: Request,
) -> SecuredSourceBriefIngestionService:
    knowledge = request.app.state.knowledge_repository
    return SecuredSourceBriefIngestionService(
        feed_items=get_feed_item_review(request),
        ingestion=request.app.state.ingestion_orchestration_service,
        repository=request.app.state.ingestion_orchestration_repository,
        knowledge=knowledge,
        processor=SourceBriefStageProcessor(knowledge),
    )


SourceBriefIngestionDep = Annotated[
    SecuredSourceBriefIngestionService,
    Depends(get_source_brief_ingestion),
]


@router.post(
    "/feed-items/{proposal_id}/source-brief",
    response_model=SourceBriefIngestionResponse,
)
def build_source_brief(
    proposal_id: UUID,
    principal: WritePrincipalDep,
    source_brief: SourceBriefIngestionDep,
) -> SourceBriefIngestionResponse:
    result = source_brief.build(principal, proposal_id)
    return SourceBriefIngestionResponse(
        normalized_artifact_id=result.normalized_artifact_id,
        run_id=result.run_id,
        source_brief_proposal_id=result.source_brief_proposal_id,
        run_state=result.run_state.value,
        proposal_review_state="PENDING",
    )


__all__ = ["router"]

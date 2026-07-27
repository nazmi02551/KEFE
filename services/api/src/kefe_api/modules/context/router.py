from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.context.service import ContextService

router = APIRouter(prefix="/v1", tags=["Context"])


class ContextSourceResponse(BaseModel):
    source_id: UUID
    title: str
    publisher: str
    source_kind: str
    url: str | None
    published_at: datetime | None


class ContextBlockResponse(BaseModel):
    context_block_id: UUID
    display_order: int
    disclosure_level: str
    title: str
    body: str
    claim_status: str
    source_ids: list[UUID]


class ContextSnapshotResponse(BaseModel):
    case_version_id: UUID
    blocks: list[ContextBlockResponse]
    sources: list[ContextSourceResponse]


def get_service(request: Request) -> ContextService:
    return request.app.state.context_service


ContextServiceDep = Annotated[ContextService, Depends(get_service)]


@router.get(
    "/case-versions/{case_version_id}/context",
    response_model=ContextSnapshotResponse,
)
def get_context(
    case_version_id: UUID,
    service: ContextServiceDep,
) -> ContextSnapshotResponse:
    snapshot = service.get_context(case_version_id)
    return ContextSnapshotResponse(
        case_version_id=snapshot.case_version_id,
        blocks=[
            ContextBlockResponse(
                context_block_id=block.id,
                display_order=block.display_order,
                disclosure_level=block.disclosure_level,
                title=block.title,
                body=block.body,
                claim_status=block.claim_status,
                source_ids=list(block.source_ids),
            )
            for block in snapshot.blocks[:20]
        ],
        sources=[
            ContextSourceResponse(
                source_id=source.id,
                title=source.title,
                publisher=source.publisher,
                source_kind=source.source_kind,
                url=source.url,
                published_at=source.published_at,
            )
            for source in snapshot.sources[:20]
        ],
    )

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.identity.dependencies import PrincipalDep
from kefe_api.modules.sharing.service import ShareService

router = APIRouter(prefix="/v1", tags=["Sharing"])


class CreateShareRequest(BaseModel):
    session_id: UUID
    include_decision: bool = False


class CreateShareResponse(BaseModel):
    share_id: UUID
    token: str
    expires_at: datetime
    include_decision: bool


class PublicShareResponse(BaseModel):
    share_id: UUID
    case_id: UUID
    case_version_id: UUID
    title: str
    summary: str
    primary_domain: str
    decision: dict[str, Any] | None
    created_at: datetime
    expires_at: datetime


def get_service(request: Request) -> ShareService:
    return request.app.state.share_service


ShareServiceDep = Annotated[ShareService, Depends(get_service)]


@router.post("/shares", status_code=201, response_model=CreateShareResponse)
def create_share(
    body: CreateShareRequest,
    principal: PrincipalDep,
    service: ShareServiceDep,
) -> CreateShareResponse:
    record, token = service.create(
        actor_id=principal.actor_id,
        session_id=body.session_id,
        include_decision=body.include_decision,
    )
    return CreateShareResponse(
        share_id=record.id,
        token=token,
        expires_at=record.expires_at,
        include_decision=record.include_decision,
    )


@router.get("/shares/{token}", response_model=PublicShareResponse)
def read_share(token: str, service: ShareServiceDep) -> PublicShareResponse:
    share = service.read_public(token)
    return PublicShareResponse(
        share_id=share.share_id,
        case_id=share.case_id,
        case_version_id=share.case_version_id,
        title=share.title,
        summary=share.summary,
        primary_domain=share.primary_domain,
        decision=share.decision,
        created_at=share.created_at,
        expires_at=share.expires_at,
    )


@router.delete("/shares/{share_id}", status_code=204)
def revoke_share(
    share_id: UUID,
    principal: PrincipalDep,
    service: ShareServiceDep,
) -> None:
    service.revoke(actor_id=principal.actor_id, share_id=share_id)

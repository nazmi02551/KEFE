from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from kefe_api.modules.identity.models import ActorPrincipal
from kefe_api.modules.identity.service import IdentityService

router = APIRouter(prefix="/v1/identity", tags=["Identity"])


class GuestCredentialResponse(BaseModel):
    actor_id: UUID
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime


def get_identity_service(request: Request) -> IdentityService:
    return request.app.state.identity_service


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def get_principal(
    authorization: AuthorizationHeader,
    service: IdentityServiceDep,
) -> ActorPrincipal:
    return service.authenticate(authorization)


PrincipalDep = Annotated[ActorPrincipal, Depends(get_principal)]


@router.post("/guest", status_code=201)
def create_guest(service: IdentityServiceDep) -> GuestCredentialResponse:
    credential = service.create_guest()
    return GuestCredentialResponse(
        actor_id=credential.actor_id,
        access_token=credential.access_token,
        expires_at=credential.expires_at,
    )


@router.delete("/session", status_code=204)
def revoke_session(
    authorization: AuthorizationHeader,
    service: IdentityServiceDep,
) -> None:
    service.authenticate(authorization)
    service.revoke(authorization)

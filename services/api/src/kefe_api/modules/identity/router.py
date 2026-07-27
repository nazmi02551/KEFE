from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from kefe_api.modules.identity.dependencies import AuthorizationHeader, IdentityServiceDep

router = APIRouter(prefix="/v1/identity", tags=["Identity"])


class GuestCredentialResponse(BaseModel):
    actor_id: UUID
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime


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

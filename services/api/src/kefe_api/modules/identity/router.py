from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from kefe_api.modules.identity.admission import ClientPlatform, GuestAdmissionContext
from kefe_api.modules.identity.dependencies import (
    AuthorizationDep,
    GuestAdmissionGuardDep,
    IdentityServiceDep,
)

router = APIRouter(prefix="/v1/identity", tags=["Identity"])


class GuestCreateRequest(BaseModel):
    platform: ClientPlatform = ClientPlatform.UNKNOWN
    integrity_evidence: str | None = Field(default=None, max_length=8192)


class GuestCredentialResponse(BaseModel):
    actor_id: UUID
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime


@router.post("/guest", status_code=201)
def create_guest(
    request: Request,
    admission: GuestAdmissionGuardDep,
    service: IdentityServiceDep,
    body: GuestCreateRequest | None = None,
) -> GuestCredentialResponse:
    payload = body or GuestCreateRequest()
    source_key = request.client.host if request.client else "unknown"
    admission.authorize(
        GuestAdmissionContext(
            source_key=source_key,
            platform=payload.platform,
            integrity_evidence=payload.integrity_evidence,
        )
    )
    credential = service.create_guest()
    return GuestCredentialResponse(
        actor_id=credential.actor_id,
        access_token=credential.access_token,
        expires_at=credential.expires_at,
    )


@router.delete("/session", status_code=204)
def revoke_session(
    authorization: AuthorizationDep,
    service: IdentityServiceDep,
) -> None:
    service.authenticate(authorization)
    service.revoke(authorization)

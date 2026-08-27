from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from kefe_api.core.settings import get_settings
from kefe_api.modules.identity.admission import ClientPlatform, GuestAdmissionContext
from kefe_api.modules.identity.dependencies import (
    AuthorizationDep,
    GuestAdmissionGuardDep,
    IdentityServiceDep,
)
from kefe_api.modules.identity.models import ActorKind
from kefe_api.modules.identity.session_renewal import SessionContinuityPolicy, SessionTokenDeriver
from kefe_api.modules.identity.session_renewal_service import SessionRenewalService

router = APIRouter(prefix="/v1/identity", tags=["Identity"])


class GuestCreateRequest(BaseModel):
    platform: ClientPlatform = ClientPlatform.UNKNOWN
    integrity_evidence: str | None = Field(default=None, max_length=8192)


class GuestCredentialResponse(BaseModel):
    actor_id: UUID
    actor_kind: ActorKind = ActorKind.GUEST
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime
    renewal_token: str | None = None
    rotation_counter: int = 0


class SessionRenewRequest(BaseModel):
    renewal_token: str = Field(min_length=32, max_length=512)


class SessionRenewResponse(BaseModel):
    actor_id: UUID
    actor_kind: ActorKind
    token_type: str = "Bearer"
    access_token: str
    access_expires_at: datetime
    renewal_token: str
    rotation_counter: int


def _renewal_service(request: Request) -> SessionRenewalService:
    settings = get_settings()
    policy = SessionContinuityPolicy.from_days(
        access_ttl_days=settings.guest_token_ttl_days,
        absolute_lifetime_days=settings.session_renewal_absolute_lifetime_days,
        inactivity_lifetime_days=settings.session_renewal_inactivity_days,
        previous_pair_grace_seconds=settings.session_renewal_previous_pair_grace_seconds,
    )
    deriver = SessionTokenDeriver(
        active_key_id=settings.session_renewal_active_key_id,
        active_secret=settings.session_renewal_secret,
        retained_keys=settings.session_renewal_retained_keys,
    )
    return SessionRenewalService(
        repository=request.app.state.identity_repository,
        policy=policy,
        deriver=deriver,
        account_access_ttl=timedelta(days=settings.account_token_ttl_days),
    )


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
        renewal_token=credential.renewal_token,
        rotation_counter=credential.rotation_counter,
    )


@router.post("/session/renew")
def renew_session(request: Request, body: SessionRenewRequest) -> SessionRenewResponse:
    credential = _renewal_service(request).renew(renewal_token=body.renewal_token)
    return SessionRenewResponse(
        actor_id=credential.actor_id,
        actor_kind=credential.actor_kind,
        access_token=credential.access_token,
        access_expires_at=credential.access_expires_at,
        renewal_token=credential.renewal_token,
        rotation_counter=credential.rotation_counter,
    )


@router.post("/session/continuity/bootstrap")
def bootstrap_session_continuity(
    request: Request,
    authorization: AuthorizationDep,
    service: IdentityServiceDep,
) -> SessionRenewResponse:
    access_token = service.require_active_access_token(authorization)
    credential = _renewal_service(request).bootstrap(access_token=access_token)
    return SessionRenewResponse(
        actor_id=credential.actor_id,
        actor_kind=credential.actor_kind,
        access_token=credential.access_token,
        access_expires_at=credential.access_expires_at,
        renewal_token=credential.renewal_token,
        rotation_counter=credential.rotation_counter,
    )


@router.delete("/session", status_code=204)
def revoke_session(
    authorization: AuthorizationDep,
    service: IdentityServiceDep,
) -> None:
    service.authenticate(authorization)
    service.revoke(authorization)

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.account_service import AccountContinuityService
from kefe_api.modules.identity.dependencies import GuestMergeAuthorizationDep
from kefe_api.modules.identity.models import ActorKind

router = APIRouter(prefix="/v1/auth", tags=["Account Continuity"])


class OtpRequest(BaseModel):
    channel: OtpChannel
    identifier: str = Field(min_length=3, max_length=254)


class OtpChallengeResponse(BaseModel):
    challenge_id: UUID
    channel: OtpChannel
    destination_hint: str
    expires_at: datetime


class OtpVerifyRequest(BaseModel):
    challenge_id: UUID
    code: str = Field(min_length=6, max_length=6)


class OtpVerificationResponse(BaseModel):
    verification_token: str
    expires_at: datetime


class GuestMergeRequest(BaseModel):
    verification_token: str = Field(min_length=16, max_length=256)


class AccountCredentialResponse(BaseModel):
    actor_id: UUID
    actor_kind: ActorKind = ActorKind.ACCOUNT
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime
    merged_from_actor_id: UUID | None = None
    renewal_token: str | None = None
    rotation_counter: int = 0


def get_service(request: Request) -> AccountContinuityService:
    return request.app.state.account_continuity_service


AccountServiceDep = Annotated[AccountContinuityService, Depends(get_service)]


@router.post("/otp/request", response_model=OtpChallengeResponse, status_code=201)
def request_otp(body: OtpRequest, service: AccountServiceDep) -> OtpChallengeResponse:
    challenge = service.request_otp(channel=body.channel, identifier=body.identifier)
    return OtpChallengeResponse(
        challenge_id=challenge.id,
        channel=challenge.channel,
        destination_hint=challenge.identifier_hint,
        expires_at=challenge.expires_at,
    )


@router.post("/otp/verify", response_model=OtpVerificationResponse)
def verify_otp(body: OtpVerifyRequest, service: AccountServiceDep) -> OtpVerificationResponse:
    token, expires_at = service.verify_otp(challenge_id=body.challenge_id, code=body.code)
    return OtpVerificationResponse(verification_token=token, expires_at=expires_at)


@router.post("/guest-merge", response_model=AccountCredentialResponse)
def merge_guest(
    body: GuestMergeRequest,
    authorization: GuestMergeAuthorizationDep,
    service: AccountServiceDep,
) -> AccountCredentialResponse:
    credential = service.merge_guest(
        authorization=authorization,
        verification_token=body.verification_token,
    )
    return AccountCredentialResponse(
        actor_id=credential.actor_id,
        access_token=credential.access_token,
        expires_at=credential.expires_at,
        merged_from_actor_id=credential.merged_from_actor_id,
        renewal_token=credential.renewal_token,
        rotation_counter=credential.rotation_counter,
    )

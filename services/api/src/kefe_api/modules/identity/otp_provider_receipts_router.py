from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.otp_provider_receipts import (
    OtpProviderReceiptOutcome,
    OtpProviderReceiptService,
)

router = APIRouter(
    prefix="/internal/provider/v1",
    tags=["Provider Callbacks"],
)


class OtpProviderReceiptBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_id: UUID
    outcome: OtpProviderReceiptOutcome
    occurred_at: datetime


class OtpProviderReceiptResponse(BaseModel):
    accepted: bool = True
    duplicate: bool


def get_service(request: Request) -> OtpProviderReceiptService:
    return request.app.state.otp_provider_receipt_service


def _rejected_error() -> DomainError:
    return DomainError(
        "AUTH_OTP_RECEIPT_REJECTED",
        "OTP provider receipt authentication failed",
        401,
        retryable=False,
    )


@router.post(
    "/otp-delivery-receipts",
    response_model=OtpProviderReceiptResponse,
    status_code=202,
    include_in_schema=False,
)
async def receive_otp_provider_receipt(
    request: Request,
    timestamp: Annotated[
        str,
        Header(alias="X-KEFE-OTP-Receipt-Timestamp"),
    ],
    key_id: Annotated[
        str,
        Header(alias="X-KEFE-OTP-Receipt-Key-Id"),
    ],
    provider_event_id: Annotated[
        str,
        Header(alias="X-KEFE-OTP-Receipt-Event-Id"),
    ],
    signature: Annotated[
        str,
        Header(alias="X-KEFE-OTP-Receipt-Signature"),
    ],
) -> OtpProviderReceiptResponse:
    service = get_service(request)
    raw_body = await request.body()
    if not raw_body or len(raw_body) > service.policy.maximum_body_bytes:
        raise _rejected_error()
    try:
        body = OtpProviderReceiptBody.model_validate_json(raw_body)
    except ValidationError as exc:
        raise _rejected_error() from exc
    if (
        body.occurred_at.tzinfo is None
        or body.occurred_at.utcoffset() != UTC.utcoffset(body.occurred_at)
    ):
        raise _rejected_error()

    result = service.receive(
        raw_body=raw_body,
        timestamp=timestamp,
        key_id=key_id,
        provider_event_id=provider_event_id,
        signature=signature,
        delivery_id=body.delivery_id,
        outcome=body.outcome,
        occurred_at=body.occurred_at,
    )
    return OtpProviderReceiptResponse(duplicate=result.duplicate)

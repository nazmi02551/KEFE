from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, ConfigDict

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


@router.post(
    "/otp-delivery-receipts",
    response_model=OtpProviderReceiptResponse,
    status_code=202,
    include_in_schema=False,
)
async def receive_otp_provider_receipt(
    body: OtpProviderReceiptBody,
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
    result = get_service(request).receive(
        raw_body=await request.body(),
        timestamp=timestamp,
        key_id=key_id,
        provider_event_id=provider_event_id,
        signature=signature,
        delivery_id=body.delivery_id,
        outcome=body.outcome,
        occurred_at=body.occurred_at,
    )
    return OtpProviderReceiptResponse(duplicate=result.duplicate)

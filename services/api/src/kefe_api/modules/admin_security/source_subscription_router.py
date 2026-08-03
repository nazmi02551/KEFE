from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.admin_security.source_subscriptions import (
    AdminRssAtomActivationView,
    AdminRssAtomSubscriptionView,
    SecuredRssAtomSubscriptionService,
)

router = APIRouter(
    prefix="/internal/admin/v1/source-subscriptions",
    tags=["Internal Admin Source Subscriptions"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceSubscriptionResponse(StrictModel):
    subscription_code: str
    adapter_code: str
    external_locator: str
    interval_seconds: int
    max_dispatch_attempts: int
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_redirect_hops: int
    locale: str | None
    jurisdiction_code: str | None
    configuration_hash: str


class SourceSubscriptionInventoryResponse(StrictModel):
    items: list[SourceSubscriptionResponse]


class ActivateSourceSubscriptionRequest(StrictModel):
    expected_configuration_hash: str = Field(
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    first_due_at: datetime


class SourceSubscriptionActivationResponse(StrictModel):
    subscription_code: str
    adapter_code: str
    configuration_hash: str
    capability_lifecycle: str
    circuit_state: str
    schedule_id: UUID
    schedule_state: str
    next_due_at: datetime


def get_source_subscriptions(
    request: Request,
) -> SecuredRssAtomSubscriptionService:
    return request.app.state.secured_rss_atom_subscription_service


SourceSubscriptionDep = Annotated[
    SecuredRssAtomSubscriptionService,
    Depends(get_source_subscriptions),
]


@router.get("", response_model=SourceSubscriptionInventoryResponse)
def list_source_subscriptions(
    principal: ReadPrincipalDep,
    subscriptions: SourceSubscriptionDep,
) -> SourceSubscriptionInventoryResponse:
    return SourceSubscriptionInventoryResponse(
        items=[
            _subscription_response(item)
            for item in subscriptions.list_subscriptions(principal)
        ]
    )


@router.post(
    "/{subscription_code}/activate",
    response_model=SourceSubscriptionActivationResponse,
)
def activate_source_subscription(
    subscription_code: str,
    body: ActivateSourceSubscriptionRequest,
    principal: WritePrincipalDep,
    subscriptions: SourceSubscriptionDep,
) -> SourceSubscriptionActivationResponse:
    return _activation_response(
        subscriptions.activate(
            principal,
            subscription_code=subscription_code,
            expected_configuration_hash=body.expected_configuration_hash,
            first_due_at=body.first_due_at,
        )
    )


def _subscription_response(
    view: AdminRssAtomSubscriptionView,
) -> SourceSubscriptionResponse:
    return SourceSubscriptionResponse(
        subscription_code=view.subscription_code,
        adapter_code=view.adapter_code,
        external_locator=view.external_locator,
        interval_seconds=view.interval_seconds,
        max_dispatch_attempts=view.max_dispatch_attempts,
        quota_limit=view.quota_limit,
        quota_window_seconds=view.quota_window_seconds,
        failure_threshold=view.failure_threshold,
        circuit_open_seconds=view.circuit_open_seconds,
        permit_ttl_seconds=view.permit_ttl_seconds,
        connect_timeout_ms=view.connect_timeout_ms,
        read_timeout_ms=view.read_timeout_ms,
        total_timeout_ms=view.total_timeout_ms,
        max_redirect_hops=view.max_redirect_hops,
        locale=view.locale,
        jurisdiction_code=view.jurisdiction_code,
        configuration_hash=view.configuration_hash,
    )


def _activation_response(
    view: AdminRssAtomActivationView,
) -> SourceSubscriptionActivationResponse:
    return SourceSubscriptionActivationResponse(
        subscription_code=view.subscription_code,
        adapter_code=view.adapter_code,
        configuration_hash=view.configuration_hash,
        capability_lifecycle=view.capability_lifecycle,
        circuit_state=view.circuit_state,
        schedule_id=view.schedule_id,
        schedule_state=view.schedule_state,
        next_due_at=view.next_due_at,
    )


__all__ = ["router"]

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.content_configuration import (
    SecuredContentConfigurationService,
)
from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.content_config.models import (
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)

router = APIRouter(prefix="/internal/admin/v1/content-configuration", tags=["Internal Admin"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfigurationInput(StrictModel):
    domains: list[str] = Field(min_length=1)
    base_formats: list[str] = Field(min_length=1)
    modifiers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(min_length=1)
    claim_states: list[str] = Field(min_length=1)
    review_modes: list[str] = Field(default_factory=list)
    allowed_modifiers: dict[str, list[str]] = Field(default_factory=dict)
    review_modes_by_risk: dict[str, list[str]] = Field(default_factory=dict)


class ConfigurationResponse(StrictModel):
    id: UUID
    version_no: int
    state: str
    domains: list[str]
    base_formats: list[str]
    modifiers: list[str]
    risks: list[str]
    claim_states: list[str]
    review_modes: list[str]
    allowed_modifiers: dict[str, list[str]]
    review_modes_by_risk: dict[str, list[str]]
    published_at: str | None


class ConfigurationAuditResponse(StrictModel):
    snapshot_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    superseded_snapshot_id: UUID | None
    occurred_at: str


def get_configuration(request: Request) -> SecuredContentConfigurationService:
    return request.app.state.secured_content_configuration_service


ConfigurationDep = Annotated[SecuredContentConfigurationService, Depends(get_configuration)]


@router.get("/current", response_model=ConfigurationResponse)
def current(
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationResponse:
    return _response(configuration.current(principal))


@router.post(
    "/drafts",
    response_model=ConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationResponse:
    return _response(configuration.create_draft(principal))


@router.get("/audit", response_model=list[ConfigurationAuditResponse])
def audit(
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> list[ConfigurationAuditResponse]:
    return [_audit_response(item) for item in configuration.audit(principal)]


@router.get("/{snapshot_id}", response_model=ConfigurationResponse)
def get_snapshot(
    snapshot_id: UUID,
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationResponse:
    return _response(configuration.get(principal, snapshot_id))


@router.put("/{snapshot_id}", response_model=ConfigurationResponse)
def save_draft(
    snapshot_id: UUID,
    body: ConfigurationInput,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationResponse:
    updated = configuration.save_draft(
        principal,
        snapshot_id,
        domains=frozenset(body.domains),
        base_formats=frozenset(body.base_formats),
        modifiers=frozenset(body.modifiers),
        risks=frozenset(body.risks),
        claim_states=frozenset(body.claim_states),
        review_modes=frozenset(body.review_modes),
        allowed_modifiers={key: frozenset(value) for key, value in body.allowed_modifiers.items()},
        review_modes_by_risk={
            key: frozenset(value) for key, value in body.review_modes_by_risk.items()
        },
    )
    return _response(updated)


@router.post("/{snapshot_id}/publish", response_model=ConfigurationResponse)
def publish(
    snapshot_id: UUID,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationResponse:
    return _response(configuration.publish(principal, snapshot_id))


def _response(snapshot: ContentConfigurationSnapshot) -> ConfigurationResponse:
    return ConfigurationResponse(
        id=snapshot.id,
        version_no=snapshot.version_no,
        state=snapshot.state.value,
        domains=sorted(snapshot.domains),
        base_formats=sorted(snapshot.base_formats),
        modifiers=sorted(snapshot.modifiers),
        risks=sorted(snapshot.risks),
        claim_states=sorted(snapshot.claim_states),
        review_modes=sorted(snapshot.review_modes),
        allowed_modifiers={
            key: sorted(value) for key, value in snapshot.allowed_modifiers.items()
        },
        review_modes_by_risk={
            key: sorted(value) for key, value in snapshot.review_modes_by_risk.items()
        },
        published_at=snapshot.published_at.isoformat() if snapshot.published_at else None,
    )


def _audit_response(item: ContentConfigurationAuditEntry) -> ConfigurationAuditResponse:
    return ConfigurationAuditResponse(
        snapshot_id=item.snapshot_id,
        actor_ref=item.actor_ref,
        command=item.command,
        previous_state=item.previous_state.value if item.previous_state else None,
        new_state=item.new_state.value,
        superseded_snapshot_id=item.superseded_snapshot_id,
        occurred_at=item.occurred_at.isoformat(),
    )

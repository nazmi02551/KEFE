from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.content_configuration import (
    SecuredContentConfigurationService,
)
from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.content_configuration.models import (
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
    FlowStepDefinition,
    FlowTemplateDefinition,
)

router = APIRouter(
    prefix="/internal/admin/v1/flow-composer",
    tags=["Internal Admin Flow Composer"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlowStepInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    primitive_code: str = Field(min_length=1, max_length=120)
    capability_codes: list[str] = Field(default_factory=list, max_length=100)
    next_step_codes: list[str] = Field(default_factory=list, max_length=100)
    payload_schema_ref: str | None = Field(default=None, max_length=500)

    def to_domain(self) -> FlowStepDefinition:
        return FlowStepDefinition(
            code=self.code,
            primitive_code=self.primitive_code,
            capability_codes=tuple(self.capability_codes),
            next_step_codes=tuple(self.next_step_codes),
            payload_schema_ref=self.payload_schema_ref,
        )


class FlowTemplateInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    version_no: int = Field(gt=0, le=1_000_000)
    label_key: str = Field(min_length=1, max_length=240)
    entry_step_code: str = Field(min_length=1, max_length=120)
    steps: list[FlowStepInput] = Field(min_length=1, max_length=200)
    enabled: bool = True

    def to_domain(self) -> FlowTemplateDefinition:
        return FlowTemplateDefinition(
            code=self.code,
            version_no=self.version_no,
            label_key=self.label_key,
            entry_step_code=self.entry_step_code,
            steps=tuple(step.to_domain() for step in self.steps),
            enabled=self.enabled,
        )


class FlowTemplatesInput(StrictModel):
    flow_templates: list[FlowTemplateInput] = Field(max_length=200)


class PrimitiveResponse(StrictModel):
    code: str
    label_key: str
    payload_schema_ref: str | None
    enabled: bool


class CapabilityResponse(StrictModel):
    code: str
    label_key: str
    compatible_primitive_codes: list[str]
    config_schema_ref: str | None
    enabled: bool


class FlowStepResponse(StrictModel):
    code: str
    primitive_code: str
    capability_codes: list[str]
    next_step_codes: list[str]
    payload_schema_ref: str | None


class FlowTemplateResponse(StrictModel):
    code: str
    version_no: int
    label_key: str
    entry_step_code: str
    steps: list[FlowStepResponse]
    enabled: bool


class FlowComposerVersionResponse(StrictModel):
    id: UUID
    version_no: int
    state: str
    primitives: list[PrimitiveResponse]
    capabilities: list[CapabilityResponse]
    flow_templates: list[FlowTemplateResponse]
    created_at: datetime
    published_at: datetime | None
    cloned_from_version_id: UUID | None


class ConfigurationAuditEntryResponse(StrictModel):
    audit_id: UUID
    config_version_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    rationale: str | None
    occurred_at: datetime


class ConfigurationAuditTrailResponse(StrictModel):
    items: list[ConfigurationAuditEntryResponse]


def get_configuration(request: Request) -> SecuredContentConfigurationService:
    return request.app.state.secured_content_configuration_service


ConfigurationDep = Annotated[
    SecuredContentConfigurationService,
    Depends(get_configuration),
]


@router.post(
    "/drafts",
    response_model=FlowComposerVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> FlowComposerVersionResponse:
    return _version_response(configuration.create_draft_from_current(principal))


@router.get(
    "/configuration-versions/{version_id}",
    response_model=FlowComposerVersionResponse,
)
def get_version(
    version_id: UUID,
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> FlowComposerVersionResponse:
    return _version_response(configuration.get_version(principal, version_id))


@router.put(
    "/configuration-versions/{version_id}",
    response_model=FlowComposerVersionResponse,
)
def save_flow_templates(
    version_id: UUID,
    body: FlowTemplatesInput,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> FlowComposerVersionResponse:
    return _version_response(
        configuration.save_flow_templates(
            principal,
            version_id,
            tuple(item.to_domain() for item in body.flow_templates),
        )
    )


@router.get(
    "/configuration-versions/{version_id}/audit",
    response_model=ConfigurationAuditTrailResponse,
)
def audit(
    version_id: UUID,
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationAuditTrailResponse:
    return ConfigurationAuditTrailResponse(
        items=[
            _audit_response(item)
            for item in configuration.audit_for_version(principal, version_id)
        ]
    )


def _version_response(
    snapshot: ContentConfigurationSnapshot,
) -> FlowComposerVersionResponse:
    return FlowComposerVersionResponse(
        id=snapshot.id,
        version_no=snapshot.version_no,
        state=snapshot.state.value,
        primitives=[
            PrimitiveResponse(
                code=item.code,
                label_key=item.label_key,
                payload_schema_ref=item.payload_schema_ref,
                enabled=item.enabled,
            )
            for item in snapshot.primitives
        ],
        capabilities=[
            CapabilityResponse(
                code=item.code,
                label_key=item.label_key,
                compatible_primitive_codes=sorted(item.compatible_primitive_codes),
                config_schema_ref=item.config_schema_ref,
                enabled=item.enabled,
            )
            for item in snapshot.capabilities
        ],
        flow_templates=[
            FlowTemplateResponse(
                code=flow.code,
                version_no=flow.version_no,
                label_key=flow.label_key,
                entry_step_code=flow.entry_step_code,
                steps=[
                    FlowStepResponse(
                        code=step.code,
                        primitive_code=step.primitive_code,
                        capability_codes=list(step.capability_codes),
                        next_step_codes=list(step.next_step_codes),
                        payload_schema_ref=step.payload_schema_ref,
                    )
                    for step in flow.steps
                ],
                enabled=flow.enabled,
            )
            for flow in snapshot.flow_templates
        ],
        created_at=snapshot.created_at,
        published_at=snapshot.published_at,
        cloned_from_version_id=snapshot.cloned_from_version_id,
    )


def _audit_response(
    entry: ContentConfigurationAuditEntry,
) -> ConfigurationAuditEntryResponse:
    return ConfigurationAuditEntryResponse(
        audit_id=entry.audit_id,
        config_version_id=entry.config_version_id,
        actor_ref=entry.actor_ref,
        command=entry.command,
        previous_state=entry.previous_state.value if entry.previous_state else None,
        new_state=entry.new_state.value,
        rationale=entry.rationale,
        occurred_at=entry.occurred_at,
    )

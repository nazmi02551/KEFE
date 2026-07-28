from __future__ import annotations

from dataclasses import replace
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
    CapabilityDefinition,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
    FlowStepDefinition,
    FlowTemplateDefinition,
    PrimitiveDefinition,
    TaxonomyItem,
    TopicItem,
)

router = APIRouter(
    prefix="/internal/admin/v1/content-configuration",
    tags=["Internal Admin Content Configuration"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaxonomyItemInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    label_key: str = Field(min_length=1, max_length=240)
    enabled: bool = True

    def to_domain(self) -> TaxonomyItem:
        return TaxonomyItem(code=self.code, label_key=self.label_key, enabled=self.enabled)


class TopicItemInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    domain_code: str = Field(min_length=1, max_length=120)
    label_key: str = Field(min_length=1, max_length=240)
    enabled: bool = True

    def to_domain(self) -> TopicItem:
        return TopicItem(
            code=self.code,
            domain_code=self.domain_code,
            label_key=self.label_key,
            enabled=self.enabled,
        )


class PrimitiveInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    label_key: str = Field(min_length=1, max_length=240)
    payload_schema_ref: str | None = Field(default=None, max_length=500)
    enabled: bool = True

    def to_domain(self) -> PrimitiveDefinition:
        return PrimitiveDefinition(
            code=self.code,
            label_key=self.label_key,
            payload_schema_ref=self.payload_schema_ref,
            enabled=self.enabled,
        )


class CapabilityInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    label_key: str = Field(min_length=1, max_length=240)
    compatible_primitive_codes: list[str] = Field(default_factory=list)
    config_schema_ref: str | None = Field(default=None, max_length=500)
    enabled: bool = True

    def to_domain(self) -> CapabilityDefinition:
        return CapabilityDefinition(
            code=self.code,
            label_key=self.label_key,
            compatible_primitive_codes=frozenset(self.compatible_primitive_codes),
            config_schema_ref=self.config_schema_ref,
            enabled=self.enabled,
        )


class FlowStepInput(StrictModel):
    code: str = Field(min_length=1, max_length=120)
    primitive_code: str = Field(min_length=1, max_length=120)
    capability_codes: list[str] = Field(default_factory=list)
    next_step_codes: list[str] = Field(default_factory=list)
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
    version_no: int = Field(gt=0)
    label_key: str = Field(min_length=1, max_length=240)
    entry_step_code: str = Field(min_length=1, max_length=120)
    steps: list[FlowStepInput] = Field(min_length=1)
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


class ConfigurationDraftInput(StrictModel):
    domains: list[TaxonomyItemInput]
    topics: list[TopicItemInput] = Field(default_factory=list)
    base_formats: list[TaxonomyItemInput]
    modifiers: list[TaxonomyItemInput]
    modifier_compatibility: dict[str, list[str]]
    primitives: list[PrimitiveInput]
    capabilities: list[CapabilityInput]
    flow_templates: list[FlowTemplateInput]
    risks: list[str]
    claim_states: list[str]
    source_kinds: list[str]
    disclosure_levels: list[str]

    def apply_to(self, current: ContentConfigurationSnapshot) -> ContentConfigurationSnapshot:
        return replace(
            current,
            domains=tuple(item.to_domain() for item in self.domains),
            topics=tuple(item.to_domain() for item in self.topics),
            base_formats=tuple(item.to_domain() for item in self.base_formats),
            modifiers=tuple(item.to_domain() for item in self.modifiers),
            modifier_compatibility={
                code: frozenset(values)
                for code, values in self.modifier_compatibility.items()
            },
            primitives=tuple(item.to_domain() for item in self.primitives),
            capabilities=tuple(item.to_domain() for item in self.capabilities),
            flow_templates=tuple(item.to_domain() for item in self.flow_templates),
            risks=frozenset(self.risks),
            claim_states=frozenset(self.claim_states),
            source_kinds=frozenset(self.source_kinds),
            disclosure_levels=frozenset(self.disclosure_levels),
        )


class RationaleRequest(StrictModel):
    rationale: str = Field(min_length=1, max_length=5000)


class TaxonomyItemResponse(StrictModel):
    code: str
    label_key: str
    enabled: bool


class TopicItemResponse(StrictModel):
    code: str
    domain_code: str
    label_key: str
    enabled: bool


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


class ConfigurationVersionResponse(StrictModel):
    id: UUID
    version_no: int
    state: str
    domains: list[TaxonomyItemResponse]
    topics: list[TopicItemResponse]
    base_formats: list[TaxonomyItemResponse]
    modifiers: list[TaxonomyItemResponse]
    modifier_compatibility: dict[str, list[str]]
    primitives: list[PrimitiveResponse]
    capabilities: list[CapabilityResponse]
    flow_templates: list[FlowTemplateResponse]
    risks: list[str]
    claim_states: list[str]
    source_kinds: list[str]
    disclosure_levels: list[str]
    created_at: datetime
    published_at: datetime | None
    cloned_from_version_id: UUID | None


class ConfigurationVersionsResponse(StrictModel):
    items: list[ConfigurationVersionResponse]


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


@router.get("/current", response_model=ConfigurationVersionResponse)
def current(
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    return _version_response(configuration.current(principal))


@router.get("/versions", response_model=ConfigurationVersionsResponse)
def list_versions(
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionsResponse:
    return ConfigurationVersionsResponse(
        items=[_version_response(item) for item in configuration.list_versions(principal)]
    )


@router.get("/versions/{version_id}", response_model=ConfigurationVersionResponse)
def get_version(
    version_id: UUID,
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    return _version_response(configuration.get_version(principal, version_id))


@router.get("/audit", response_model=ConfigurationAuditTrailResponse)
def audit(
    principal: ReadPrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationAuditTrailResponse:
    return ConfigurationAuditTrailResponse(
        items=[_audit_response(item) for item in configuration.audit_trail(principal)]
    )


@router.post(
    "/drafts",
    response_model=ConfigurationVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    return _version_response(configuration.create_draft_from_current(principal))


@router.put("/versions/{version_id}", response_model=ConfigurationVersionResponse)
def save_draft(
    version_id: UUID,
    body: ConfigurationDraftInput,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    current_draft = configuration.draft_for_edit(principal, version_id)
    updated = body.apply_to(current_draft)
    return _version_response(configuration.save_draft(principal, updated))


@router.post(
    "/versions/{version_id}/publish",
    response_model=ConfigurationVersionResponse,
)
def publish(
    version_id: UUID,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    return _version_response(configuration.publish(principal, version_id))


@router.post(
    "/versions/{version_id}/rollback-drafts",
    response_model=ConfigurationVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rollback_draft(
    version_id: UUID,
    body: RationaleRequest,
    principal: WritePrincipalDep,
    configuration: ConfigurationDep,
) -> ConfigurationVersionResponse:
    return _version_response(
        configuration.create_rollback_draft(
            principal,
            version_id,
            rationale=body.rationale,
        )
    )


def _version_response(snapshot: ContentConfigurationSnapshot) -> ConfigurationVersionResponse:
    return ConfigurationVersionResponse(
        id=snapshot.id,
        version_no=snapshot.version_no,
        state=snapshot.state.value,
        domains=[
            TaxonomyItemResponse(code=item.code, label_key=item.label_key, enabled=item.enabled)
            for item in snapshot.domains
        ],
        topics=[
            TopicItemResponse(
                code=item.code,
                domain_code=item.domain_code,
                label_key=item.label_key,
                enabled=item.enabled,
            )
            for item in snapshot.topics
        ],
        base_formats=[
            TaxonomyItemResponse(code=item.code, label_key=item.label_key, enabled=item.enabled)
            for item in snapshot.base_formats
        ],
        modifiers=[
            TaxonomyItemResponse(code=item.code, label_key=item.label_key, enabled=item.enabled)
            for item in snapshot.modifiers
        ],
        modifier_compatibility={
            code: sorted(values) for code, values in snapshot.modifier_compatibility.items()
        },
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
        risks=sorted(snapshot.risks),
        claim_states=sorted(snapshot.claim_states),
        source_kinds=sorted(snapshot.source_kinds),
        disclosure_levels=sorted(snapshot.disclosure_levels),
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

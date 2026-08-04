from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request, status
from pydantic import Field

from kefe_api.modules.admin_security.router import (
    ReadPrincipalDep,
    StrictModel,
    WritePrincipalDep,
)
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedCatalogService,
    CanonicalPublicFeedDefinition,
    PublicFeedActivationProjection,
    PublicFeedAuditEvent,
    PublicFeedPreflightResult,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])

FeedCodePath = Annotated[str, Path(min_length=1, max_length=128)]
DefinitionVersionPath = Annotated[int, Path(ge=1)]


class RssAtomParseProfileInput(StrictModel):
    accepted_media_types: list[str] = Field(
        default_factory=lambda: [
            "application/atom+xml",
            "application/rss+xml",
            "application/xml",
            "text/xml",
        ],
        min_length=1,
        max_length=16,
    )
    max_document_bytes: int = Field(default=1_048_576, ge=1, le=10_485_760)
    max_elements: int = Field(default=4096, ge=1, le=100_000)
    max_depth: int = Field(default=16, ge=1, le=64)
    max_items: int = Field(default=256, ge=0, le=10_000)
    max_node_text_chars: int = Field(default=16_384, ge=1, le=4_000_000)
    max_total_text_chars: int = Field(default=262_144, ge=1, le=4_000_000)
    max_attributes_per_element: int = Field(default=8, ge=0, le=128)
    max_total_attribute_chars: int = Field(default=65_536, ge=0, le=1_000_000)
    max_metadata_field_chars: int = Field(default=4096, ge=1, le=65_536)

    def to_domain(self) -> StrictRssAtomParseProfile:
        return StrictRssAtomParseProfile(
            accepted_media_types=tuple(self.accepted_media_types),
            max_document_bytes=self.max_document_bytes,
            max_elements=self.max_elements,
            max_depth=self.max_depth,
            max_items=self.max_items,
            max_node_text_chars=self.max_node_text_chars,
            max_total_text_chars=self.max_total_text_chars,
            max_attributes_per_element=self.max_attributes_per_element,
            max_total_attribute_chars=self.max_total_attribute_chars,
            max_metadata_field_chars=self.max_metadata_field_chars,
        )


class RegisterPublicFeedRequest(StrictModel):
    definition_version: int = Field(ge=1)
    feed_code: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=160)
    adapter_code: str = Field(min_length=1, max_length=160)
    external_locator: str = Field(min_length=1, max_length=4096)
    parser_profile: RssAtomParseProfileInput = Field(
        default_factory=RssAtomParseProfileInput
    )
    connect_timeout_ms: int = Field(ge=50, le=30_000)
    read_timeout_ms: int = Field(ge=50, le=30_000)
    total_timeout_ms: int = Field(ge=50, le=120_000)
    max_response_bytes: int = Field(ge=1, le=10_485_760)
    max_redirect_hops: int = Field(ge=0, le=5)
    terms_evidence_ref: str = Field(min_length=1, max_length=4096)
    rate_limit_evidence_ref: str = Field(min_length=1, max_length=4096)
    quota_limit: int = Field(ge=1, le=100_000)
    quota_window_seconds: int = Field(ge=1, le=86_400)
    failure_threshold: int = Field(ge=1, le=1000)
    circuit_open_seconds: int = Field(ge=1, le=86_400)
    permit_ttl_seconds: int = Field(ge=5, le=3600)
    interval_seconds: int = Field(ge=60, le=31_536_000)
    max_dispatch_attempts: int = Field(ge=1, le=20)
    language_code: str | None = Field(default=None, min_length=1, max_length=32)
    jurisdiction_code: str | None = Field(default=None, min_length=1, max_length=32)

    def to_definition(self) -> PublicFeedDefinition:
        return PublicFeedDefinition(
            feed_code=self.feed_code,
            display_name=self.display_name,
            adapter_code=self.adapter_code,
            external_locator=self.external_locator,
            parser_profile=self.parser_profile.to_domain(),
            connect_timeout_ms=self.connect_timeout_ms,
            read_timeout_ms=self.read_timeout_ms,
            total_timeout_ms=self.total_timeout_ms,
            max_response_bytes=self.max_response_bytes,
            max_redirect_hops=self.max_redirect_hops,
            terms_evidence_ref=self.terms_evidence_ref,
            rate_limit_evidence_ref=self.rate_limit_evidence_ref,
            quota_limit=self.quota_limit,
            quota_window_seconds=self.quota_window_seconds,
            failure_threshold=self.failure_threshold,
            circuit_open_seconds=self.circuit_open_seconds,
            permit_ttl_seconds=self.permit_ttl_seconds,
            language_code=self.language_code,
            jurisdiction_code=self.jurisdiction_code,
        )


class ExpectedHashRequest(StrictModel):
    expected_configuration_hash: str = Field(
        min_length=71,
        max_length=71,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )


class ActivatePublicFeedRequest(ExpectedHashRequest):
    first_due_at: datetime


class RssAtomParseProfileResponse(StrictModel):
    accepted_media_types: list[str]
    max_document_bytes: int
    max_elements: int
    max_depth: int
    max_items: int
    max_node_text_chars: int
    max_total_text_chars: int
    max_attributes_per_element: int
    max_total_attribute_chars: int
    max_metadata_field_chars: int


class PublicFeedDefinitionResponse(StrictModel):
    id: UUID
    feed_code: str
    definition_version: int
    display_name: str
    adapter_code: str
    external_locator: str
    parser_profile: RssAtomParseProfileResponse
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_response_bytes: int
    max_redirect_hops: int
    terms_evidence_ref: str
    rate_limit_evidence_ref: str
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    interval_seconds: int
    max_dispatch_attempts: int
    language_code: str | None
    jurisdiction_code: str | None
    configuration_hash: str
    state: str
    created_at: datetime
    created_by_actor_ref: str
    preflighted_at: datetime | None
    preflighted_by_actor_ref: str | None
    approved_at: datetime | None
    approved_by_actor_ref: str | None
    retired_at: datetime | None
    retired_by_actor_ref: str | None


class PublicFeedDefinitionListResponse(StrictModel):
    items: list[PublicFeedDefinitionResponse]


class PublicFeedPreflightResponse(StrictModel):
    feed_definition_id: UUID
    configuration_hash: str
    adapter_code: str
    external_locator: str
    allowed_origin: str
    pipeline_code: str
    pipeline_version: str
    interval_seconds: int
    max_dispatch_attempts: int


class PublicFeedActivationResponse(StrictModel):
    id: UUID
    feed_definition_id: UUID
    feed_code: str
    definition_version: int
    configuration_hash: str
    adapter_code: str
    schedule_id: UUID
    state: str
    activated_at: datetime
    activated_by_actor_ref: str
    updated_at: datetime
    updated_by_actor_ref: str


class PublicFeedAuditResponse(StrictModel):
    sequence: int
    definition_id: UUID
    activation_id: UUID | None
    action: str
    actor_ref: str
    occurred_at: datetime
    configuration_hash: str


class PublicFeedAuditListResponse(StrictModel):
    items: list[PublicFeedAuditResponse]


def get_canonical_public_feed_service(
    request: Request,
) -> CanonicalPublicFeedCatalogService:
    return request.app.state.canonical_public_feed_service


CanonicalPublicFeedDep = Annotated[
    CanonicalPublicFeedCatalogService,
    Depends(get_canonical_public_feed_service),
]


@router.get("/public-feeds", response_model=PublicFeedDefinitionListResponse)
def list_public_feeds(
    principal: ReadPrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedDefinitionListResponse:
    return PublicFeedDefinitionListResponse(
        items=[_definition_response(item) for item in service.list_definitions(principal)]
    )


@router.post(
    "/public-feeds",
    response_model=PublicFeedDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_public_feed(
    body: RegisterPublicFeedRequest,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedDefinitionResponse:
    created = service.register_draft(
        principal,
        definition_version=body.definition_version,
        definition=body.to_definition(),
        interval_seconds=body.interval_seconds,
        max_dispatch_attempts=body.max_dispatch_attempts,
    )
    return _definition_response(created)


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/preflight",
    response_model=PublicFeedPreflightResponse,
)
def preflight_public_feed(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedPreflightResponse:
    result = service.preflight(
        principal,
        feed_code=feed_code,
        definition_version=definition_version,
    )
    return _preflight_response(result)


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/approve",
    response_model=PublicFeedDefinitionResponse,
)
def approve_public_feed(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    body: ExpectedHashRequest,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedDefinitionResponse:
    approved = service.approve(
        principal,
        feed_code=feed_code,
        definition_version=definition_version,
        expected_configuration_hash=body.expected_configuration_hash,
    )
    return _definition_response(approved)


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/activate",
    response_model=PublicFeedActivationResponse,
)
def activate_public_feed(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    body: ActivatePublicFeedRequest,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedActivationResponse:
    activated = service.activate(
        principal,
        feed_code=feed_code,
        definition_version=definition_version,
        expected_configuration_hash=body.expected_configuration_hash,
        first_due_at=body.first_due_at,
    )
    return _activation_response(activated)


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/pause",
    response_model=PublicFeedActivationResponse,
)
def pause_public_feed(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedActivationResponse:
    return _activation_response(
        service.pause(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
        )
    )


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/resume",
    response_model=PublicFeedActivationResponse,
)
def resume_public_feed(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedActivationResponse:
    return _activation_response(
        service.resume(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
        )
    )


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/retire-activation",
    response_model=PublicFeedActivationResponse,
)
def retire_public_feed_activation(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedActivationResponse:
    return _activation_response(
        service.retire_activation(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
        )
    )


@router.post(
    "/public-feeds/{feed_code}/versions/{definition_version}/retire-definition",
    response_model=PublicFeedDefinitionResponse,
)
def retire_public_feed_definition(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: WritePrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedDefinitionResponse:
    return _definition_response(
        service.retire_definition(
            principal,
            feed_code=feed_code,
            definition_version=definition_version,
        )
    )


@router.get(
    "/public-feeds/{feed_code}/versions/{definition_version}/audit",
    response_model=PublicFeedAuditListResponse,
)
def public_feed_audit(
    feed_code: FeedCodePath,
    definition_version: DefinitionVersionPath,
    principal: ReadPrincipalDep,
    service: CanonicalPublicFeedDep,
) -> PublicFeedAuditListResponse:
    return PublicFeedAuditListResponse(
        items=[
            _audit_response(item)
            for item in service.audit(
                principal,
                feed_code=feed_code,
                definition_version=definition_version,
            )
        ]
    )


def _definition_response(
    item: CanonicalPublicFeedDefinition,
) -> PublicFeedDefinitionResponse:
    definition = item.definition
    profile = definition.parser_profile
    return PublicFeedDefinitionResponse(
        id=item.id,
        feed_code=item.feed_code,
        definition_version=item.definition_version,
        display_name=definition.display_name,
        adapter_code=definition.adapter_code,
        external_locator=definition.external_locator,
        parser_profile=RssAtomParseProfileResponse(
            accepted_media_types=list(profile.accepted_media_types),
            max_document_bytes=profile.max_document_bytes,
            max_elements=profile.max_elements,
            max_depth=profile.max_depth,
            max_items=profile.max_items,
            max_node_text_chars=profile.max_node_text_chars,
            max_total_text_chars=profile.max_total_text_chars,
            max_attributes_per_element=profile.max_attributes_per_element,
            max_total_attribute_chars=profile.max_total_attribute_chars,
            max_metadata_field_chars=profile.max_metadata_field_chars,
        ),
        connect_timeout_ms=definition.connect_timeout_ms,
        read_timeout_ms=definition.read_timeout_ms,
        total_timeout_ms=definition.total_timeout_ms,
        max_response_bytes=definition.max_response_bytes,
        max_redirect_hops=definition.max_redirect_hops,
        terms_evidence_ref=definition.terms_evidence_ref,
        rate_limit_evidence_ref=definition.rate_limit_evidence_ref,
        quota_limit=definition.quota_limit,
        quota_window_seconds=definition.quota_window_seconds,
        failure_threshold=definition.failure_threshold,
        circuit_open_seconds=definition.circuit_open_seconds,
        permit_ttl_seconds=definition.permit_ttl_seconds,
        interval_seconds=item.interval_seconds,
        max_dispatch_attempts=item.max_dispatch_attempts,
        language_code=definition.language_code,
        jurisdiction_code=definition.jurisdiction_code,
        configuration_hash=item.configuration_hash,
        state=item.state.value,
        created_at=item.created_at,
        created_by_actor_ref=item.created_by_actor_ref,
        preflighted_at=item.preflighted_at,
        preflighted_by_actor_ref=item.preflighted_by_actor_ref,
        approved_at=item.approved_at,
        approved_by_actor_ref=item.approved_by_actor_ref,
        retired_at=item.retired_at,
        retired_by_actor_ref=item.retired_by_actor_ref,
    )


def _preflight_response(
    item: PublicFeedPreflightResult,
) -> PublicFeedPreflightResponse:
    return PublicFeedPreflightResponse(
        feed_definition_id=item.feed_definition_id,
        configuration_hash=item.configuration_hash,
        adapter_code=item.adapter_code,
        external_locator=item.external_locator,
        allowed_origin=item.allowed_origin,
        pipeline_code=item.pipeline_code,
        pipeline_version=item.pipeline_version,
        interval_seconds=item.interval_seconds,
        max_dispatch_attempts=item.max_dispatch_attempts,
    )


def _activation_response(
    item: PublicFeedActivationProjection,
) -> PublicFeedActivationResponse:
    return PublicFeedActivationResponse(
        id=item.id,
        feed_definition_id=item.feed_definition_id,
        feed_code=item.feed_code,
        definition_version=item.definition_version,
        configuration_hash=item.configuration_hash,
        adapter_code=item.adapter_code,
        schedule_id=item.schedule_id,
        state=item.state.value,
        activated_at=item.activated_at,
        activated_by_actor_ref=item.activated_by_actor_ref,
        updated_at=item.updated_at,
        updated_by_actor_ref=item.updated_by_actor_ref,
    )


def _audit_response(item: PublicFeedAuditEvent) -> PublicFeedAuditResponse:
    return PublicFeedAuditResponse(
        sequence=item.sequence,
        definition_id=item.definition_id,
        activation_id=item.activation_id,
        action=item.action.value,
        actor_ref=item.actor_ref,
        occurred_at=item.occurred_at,
        configuration_hash=item.configuration_hash,
    )


__all__ = ["router"]

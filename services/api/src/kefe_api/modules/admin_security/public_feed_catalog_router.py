from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import Field

from kefe_api.modules.admin_security.router import (
    ReadPrincipalDep,
    StrictModel,
    WritePrincipalDep,
)
from kefe_api.modules.knowledge.public_feed_catalog import (
    PublicFeedCatalogAuditEntry,
    PublicFeedCatalogEntry,
    PublicFeedCatalogService,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

router = APIRouter(
    prefix="/internal/admin/v1/public-feeds",
    tags=["Internal Admin Public Feeds"],
)


class RssAtomParseProfileInput(StrictModel):
    accepted_media_types: list[str] = Field(min_length=1, max_length=16)
    max_document_bytes: int = Field(ge=1, le=8_388_608)
    max_elements: int = Field(ge=1, le=100_000)
    max_depth: int = Field(ge=1, le=64)
    max_items: int = Field(ge=0, le=10_000)
    max_node_text_chars: int = Field(ge=1, le=4_000_000)
    max_total_text_chars: int = Field(ge=1, le=4_000_000)
    max_attributes_per_element: int = Field(ge=0, le=128)
    max_total_attribute_chars: int = Field(ge=0, le=1_000_000)
    max_metadata_field_chars: int = Field(ge=1, le=16_384)

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
    feed_code: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=160)
    adapter_code: str = Field(min_length=1, max_length=128)
    external_locator: str = Field(min_length=1, max_length=4096)
    parser_profile: RssAtomParseProfileInput
    connect_timeout_ms: int = Field(ge=50, le=30_000)
    read_timeout_ms: int = Field(ge=50, le=30_000)
    total_timeout_ms: int = Field(ge=50, le=120_000)
    max_response_bytes: int = Field(ge=1, le=8_388_608)
    max_redirect_hops: int = Field(ge=0, le=10)
    terms_evidence_ref: str = Field(min_length=1, max_length=1000)
    rate_limit_evidence_ref: str = Field(min_length=1, max_length=1000)
    quota_limit: int = Field(ge=1, le=1_000_000)
    quota_window_seconds: int = Field(ge=1, le=86_400)
    failure_threshold: int = Field(ge=1, le=10_000)
    circuit_open_seconds: int = Field(ge=1, le=86_400)
    permit_ttl_seconds: int = Field(ge=1, le=3600)
    language_code: str | None = Field(default=None, min_length=1, max_length=32)
    jurisdiction_code: str | None = Field(default=None, min_length=1, max_length=32)

    def to_domain(self) -> PublicFeedDefinition:
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


class RetirementRequest(StrictModel):
    rationale: str = Field(min_length=1, max_length=5000)


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


class PublicFeedCatalogEntryResponse(StrictModel):
    id: UUID
    feed_code: str
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
    language_code: str | None
    jurisdiction_code: str | None
    configuration_hash: str
    state: str
    registered_by: str
    registered_at: datetime
    approved_by: str | None
    approved_at: datetime | None
    retired_by: str | None
    retired_at: datetime | None
    retirement_rationale: str | None


class PublicFeedCatalogListResponse(StrictModel):
    items: list[PublicFeedCatalogEntryResponse]


class PublicFeedCatalogAuditResponse(StrictModel):
    audit_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    occurred_at: datetime
    rationale: str | None


class PublicFeedCatalogAuditListResponse(StrictModel):
    items: list[PublicFeedCatalogAuditResponse]


def get_catalog_service(request: Request) -> PublicFeedCatalogService:
    return request.app.state.public_feed_catalog_service


CatalogDep = Annotated[PublicFeedCatalogService, Depends(get_catalog_service)]


@router.get("", response_model=PublicFeedCatalogListResponse)
def list_public_feeds(
    principal: ReadPrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogListResponse:
    return PublicFeedCatalogListResponse(
        items=[_entry_response(item) for item in catalog.list_entries(principal)]
    )


@router.get("/audit", response_model=PublicFeedCatalogAuditListResponse)
def list_public_feed_audit(
    principal: ReadPrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogAuditListResponse:
    return PublicFeedCatalogAuditListResponse(
        items=[_audit_response(item) for item in catalog.list_audit(principal)]
    )


@router.get("/{entry_id}", response_model=PublicFeedCatalogEntryResponse)
def public_feed_detail(
    entry_id: UUID,
    principal: ReadPrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogEntryResponse:
    return _entry_response(catalog.get(principal, entry_id))


@router.get(
    "/{entry_id}/audit",
    response_model=PublicFeedCatalogAuditListResponse,
)
def public_feed_audit(
    entry_id: UUID,
    principal: ReadPrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogAuditListResponse:
    catalog.get(principal, entry_id)
    return PublicFeedCatalogAuditListResponse(
        items=[
            _audit_response(item)
            for item in catalog.list_audit(principal, entry_id)
        ]
    )


@router.post(
    "",
    response_model=PublicFeedCatalogEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_public_feed(
    body: RegisterPublicFeedRequest,
    principal: WritePrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogEntryResponse:
    return _entry_response(catalog.register(principal, body.to_domain()))


@router.post(
    "/{entry_id}/approve-manual-capture",
    response_model=PublicFeedCatalogEntryResponse,
)
def approve_public_feed_manual_capture(
    entry_id: UUID,
    principal: WritePrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogEntryResponse:
    return _entry_response(catalog.approve_manual_capture(principal, entry_id))


@router.post(
    "/{entry_id}/retire",
    response_model=PublicFeedCatalogEntryResponse,
)
def retire_public_feed(
    entry_id: UUID,
    body: RetirementRequest,
    principal: WritePrincipalDep,
    catalog: CatalogDep,
) -> PublicFeedCatalogEntryResponse:
    return _entry_response(
        catalog.retire(principal, entry_id, rationale=body.rationale)
    )


def _entry_response(entry: PublicFeedCatalogEntry) -> PublicFeedCatalogEntryResponse:
    definition = entry.definition
    profile = definition.parser_profile
    return PublicFeedCatalogEntryResponse(
        id=entry.id,
        feed_code=definition.feed_code,
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
        language_code=definition.language_code,
        jurisdiction_code=definition.jurisdiction_code,
        configuration_hash=entry.configuration_hash,
        state=entry.state.value,
        registered_by=entry.registered_by,
        registered_at=entry.registered_at,
        approved_by=entry.approved_by,
        approved_at=entry.approved_at,
        retired_by=entry.retired_by,
        retired_at=entry.retired_at,
        retirement_rationale=entry.retirement_rationale,
    )


def _audit_response(
    audit: PublicFeedCatalogAuditEntry,
) -> PublicFeedCatalogAuditResponse:
    return PublicFeedCatalogAuditResponse(
        audit_id=audit.audit_id,
        catalog_entry_id=audit.catalog_entry_id,
        feed_code=audit.feed_code,
        actor_ref=audit.actor_ref,
        command=audit.command,
        previous_state=(
            audit.previous_state.value if audit.previous_state is not None else None
        ),
        new_state=audit.new_state.value,
        occurred_at=audit.occurred_at,
        rationale=audit.rationale,
    )

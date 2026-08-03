from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request

from kefe_api.modules.admin_security.public_feed_activation_catalog import (
    SecuredPublicFeedActivationCatalogService,
)
from kefe_api.modules.admin_security.router import ReadPrincipalDep, StrictModel
from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    MAX_CATALOG_PAGE_SIZE,
    PublicFeedActivationCatalogEntry,
)

_VERSIONED_CODE_PATTERN = (
    r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*\.v[1-9][0-9]*$"
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class PublicFeedActivationCatalogItemResponse(StrictModel):
    id: UUID
    activation_code: str
    adapter_code: str
    configuration_hash: str
    manifest_schema_version: str
    evidence_ref: str
    recorded_by: str
    recorded_at: datetime


class PublicFeedActivationCatalogDetailResponse(
    PublicFeedActivationCatalogItemResponse
):
    manifest: dict[str, Any]


class PublicFeedActivationCatalogListResponse(StrictModel):
    items: list[PublicFeedActivationCatalogItemResponse]
    next_cursor: str | None


def get_public_feed_activation_catalog(
    request: Request,
) -> SecuredPublicFeedActivationCatalogService:
    return request.app.state.secured_public_feed_activation_catalog_service


PublicFeedActivationCatalogDep = Annotated[
    SecuredPublicFeedActivationCatalogService,
    Depends(get_public_feed_activation_catalog),
]


@router.get(
    "/public-feed-activations",
    response_model=PublicFeedActivationCatalogListResponse,
)
def list_public_feed_activations(
    principal: ReadPrincipalDep,
    catalog: PublicFeedActivationCatalogDep,
    limit: Annotated[int, Query(ge=1, le=MAX_CATALOG_PAGE_SIZE)] = 50,
    after_activation_code: Annotated[
        str | None,
        Query(min_length=4, max_length=128, pattern=_VERSIONED_CODE_PATTERN),
    ] = None,
) -> PublicFeedActivationCatalogListResponse:
    entries = catalog.list_entries(
        principal,
        limit=limit + 1 if limit < MAX_CATALOG_PAGE_SIZE else limit,
        after_activation_code=after_activation_code,
    )
    visible = entries[:limit]
    next_cursor = (
        visible[-1].activation_code
        if len(entries) > limit and visible
        else None
    )
    return PublicFeedActivationCatalogListResponse(
        items=[_item_response(entry) for entry in visible],
        next_cursor=next_cursor,
    )


@router.get(
    "/public-feed-activations/{activation_code}",
    response_model=PublicFeedActivationCatalogDetailResponse,
)
def public_feed_activation_detail(
    activation_code: Annotated[
        str,
        Path(min_length=4, max_length=128, pattern=_VERSIONED_CODE_PATTERN),
    ],
    principal: ReadPrincipalDep,
    catalog: PublicFeedActivationCatalogDep,
) -> PublicFeedActivationCatalogDetailResponse:
    entry = catalog.detail(principal, activation_code)
    return PublicFeedActivationCatalogDetailResponse(
        **_item_response(entry).model_dump(),
        manifest=entry.manifest_payload(),
    )


def _item_response(
    entry: PublicFeedActivationCatalogEntry,
) -> PublicFeedActivationCatalogItemResponse:
    return PublicFeedActivationCatalogItemResponse(
        id=entry.id,
        activation_code=entry.activation_code,
        adapter_code=entry.adapter_code,
        configuration_hash=entry.configuration_hash,
        manifest_schema_version=entry.manifest_schema_version,
        evidence_ref=entry.evidence_ref,
        recorded_by=entry.recorded_by,
        recorded_at=entry.recorded_at,
    )


__all__ = ["router"]

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.case_media import SecuredCaseMediaService
from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.case_media.models import (
    CaseMediaProjection,
    MediaAsset,
    MediaAssetWriteResult,
    MediaAuditEntry,
    MediaBinding,
    MediaBindingWriteResult,
    MediaKind,
    MediaSlot,
    MediaState,
)

router = APIRouter(
    prefix="/internal/admin/v1/case-media",
    tags=["Internal Admin Case Media"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterMediaRequest(StrictModel):
    asset_key: str = Field(min_length=3, max_length=128)
    kind: MediaKind
    delivery_ref: str = Field(min_length=3, max_length=512)
    content_hash: str = Field(min_length=64, max_length=64)
    byte_length: int = Field(ge=1, le=1_073_741_824)
    media_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    alt_text: str = Field(min_length=1, max_length=500)
    caption: str | None = Field(default=None, max_length=1000)
    credit_label: str = Field(min_length=1, max_length=200)
    source_label: str = Field(min_length=1, max_length=300)
    poster_asset_key: str | None = Field(default=None, max_length=128)


class BindMediaRequest(StrictModel):
    case_version_id: UUID
    slot: MediaSlot
    priority: int = Field(ge=1, le=1_000_000)
    autoplay: bool = False
    muted: bool = False
    looping: bool = False


class MediaAssetResponse(StrictModel):
    media_asset_id: UUID
    asset_key: str
    kind: str
    delivery_ref: str
    content_hash: str
    byte_length: int
    media_type: str
    title: str
    alt_text: str
    caption: str | None
    credit_label: str
    source_label: str
    poster_asset_key: str | None
    state: str
    registered_by: str
    registered_at: datetime


class MediaAssetWriteResponse(StrictModel):
    asset: MediaAssetResponse
    replayed: bool


class MediaInventoryResponse(StrictModel):
    items: list[MediaAssetResponse]


class MediaAuditResponse(StrictModel):
    audit_id: UUID
    media_asset_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    occurred_at: datetime


class MediaAuditTrailResponse(StrictModel):
    items: list[MediaAuditResponse]


class MediaBindingResponse(StrictModel):
    binding_id: UUID
    case_version_id: UUID
    media_asset_id: UUID
    slot: str
    priority: int
    autoplay: bool
    muted: bool
    looping: bool
    bound_by: str
    bound_at: datetime


class MediaBindingWriteResponse(StrictModel):
    binding: MediaBindingResponse
    replayed: bool


class CaseMediaProjectionResponse(StrictModel):
    asset_key: str
    kind: str
    slot: str
    delivery_ref: str
    title: str
    alt_text: str
    caption: str | None
    credit_label: str
    source_label: str
    poster_asset_key: str | None
    autoplay: bool
    muted: bool
    looping: bool
    priority: int


class CaseMediaProjectionListResponse(StrictModel):
    items: list[CaseMediaProjectionResponse]
    preview_fallback: bool = False


def get_media(request: Request) -> SecuredCaseMediaService:
    return request.app.state.secured_case_media_service


MediaDep = Annotated[SecuredCaseMediaService, Depends(get_media)]


@router.get("", response_model=MediaInventoryResponse)
def inventory(
    principal: ReadPrincipalDep,
    media: MediaDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    state: MediaState | None = None,
) -> MediaInventoryResponse:
    return MediaInventoryResponse(
        items=[
            _asset_response(item)
            for item in media.list_assets(
                principal,
                limit=limit,
                offset=offset,
                state=state,
            )
        ]
    )


@router.post(
    "",
    response_model=MediaAssetWriteResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegisterMediaRequest,
    principal: WritePrincipalDep,
    media: MediaDep,
) -> MediaAssetWriteResponse:
    return _asset_write_response(media.register(principal, **body.model_dump()))


@router.get("/{media_asset_id}", response_model=MediaAssetResponse)
def detail(
    media_asset_id: UUID,
    principal: ReadPrincipalDep,
    media: MediaDep,
) -> MediaAssetResponse:
    return _asset_response(media.get_asset(principal, media_asset_id))


@router.get("/{media_asset_id}/audit", response_model=MediaAuditTrailResponse)
def audit(
    media_asset_id: UUID,
    principal: ReadPrincipalDep,
    media: MediaDep,
) -> MediaAuditTrailResponse:
    return MediaAuditTrailResponse(
        items=[
            _audit_response(item)
            for item in media.list_audit(principal, media_asset_id)
        ]
    )


@router.post("/{media_asset_id}/ready", response_model=MediaAssetWriteResponse)
def mark_ready(
    media_asset_id: UUID,
    principal: WritePrincipalDep,
    media: MediaDep,
) -> MediaAssetWriteResponse:
    return _asset_write_response(media.mark_ready(principal, media_asset_id))


@router.post("/{media_asset_id}/bindings", response_model=MediaBindingWriteResponse)
def bind(
    media_asset_id: UUID,
    body: BindMediaRequest,
    principal: WritePrincipalDep,
    media: MediaDep,
) -> MediaBindingWriteResponse:
    return _binding_write_response(
        media.bind(principal, media_asset_id=media_asset_id, **body.model_dump())
    )


@router.post("/{media_asset_id}/retire", response_model=MediaAssetWriteResponse)
def retire(
    media_asset_id: UUID,
    principal: WritePrincipalDep,
    media: MediaDep,
) -> MediaAssetWriteResponse:
    return _asset_write_response(media.retire(principal, media_asset_id))


@router.get(
    "/case-versions/{case_version_id}/projection",
    response_model=CaseMediaProjectionListResponse,
)
def projection(
    case_version_id: UUID,
    principal: ReadPrincipalDep,
    media: MediaDep,
) -> CaseMediaProjectionListResponse:
    return CaseMediaProjectionListResponse(
        items=[
            _projection_response(item)
            for item in media.project(principal, case_version_id)
        ]
    )


def _asset_response(item: MediaAsset) -> MediaAssetResponse:
    return MediaAssetResponse(
        media_asset_id=item.media_asset_id,
        asset_key=item.asset_key,
        kind=item.kind.value,
        delivery_ref=item.delivery_ref,
        content_hash=item.content_hash,
        byte_length=item.byte_length,
        media_type=item.media_type,
        title=item.title,
        alt_text=item.alt_text,
        caption=item.caption,
        credit_label=item.credit_label,
        source_label=item.source_label,
        poster_asset_key=item.poster_asset_key,
        state=item.state.value,
        registered_by=item.registered_by,
        registered_at=item.registered_at,
    )


def _asset_write_response(result: MediaAssetWriteResult) -> MediaAssetWriteResponse:
    return MediaAssetWriteResponse(
        asset=_asset_response(result.asset),
        replayed=result.replayed,
    )


def _binding_response(item: MediaBinding) -> MediaBindingResponse:
    return MediaBindingResponse(
        binding_id=item.binding_id,
        case_version_id=item.case_version_id,
        media_asset_id=item.media_asset_id,
        slot=item.slot.value,
        priority=item.priority,
        autoplay=item.autoplay,
        muted=item.muted,
        looping=item.looping,
        bound_by=item.bound_by,
        bound_at=item.bound_at,
    )


def _binding_write_response(
    result: MediaBindingWriteResult,
) -> MediaBindingWriteResponse:
    return MediaBindingWriteResponse(
        binding=_binding_response(result.binding),
        replayed=result.replayed,
    )


def _audit_response(item: MediaAuditEntry) -> MediaAuditResponse:
    return MediaAuditResponse(
        audit_id=item.audit_id,
        media_asset_id=item.media_asset_id,
        actor_ref=item.actor_ref,
        command=item.command,
        previous_state=(
            None if item.previous_state is None else item.previous_state.value
        ),
        new_state=item.new_state.value,
        occurred_at=item.occurred_at,
    )


def _projection_response(item: CaseMediaProjection) -> CaseMediaProjectionResponse:
    return CaseMediaProjectionResponse(
        asset_key=item.asset_key,
        kind=item.kind.value,
        slot=item.slot.value,
        delivery_ref=item.delivery_ref,
        title=item.title,
        alt_text=item.alt_text,
        caption=item.caption,
        credit_label=item.credit_label,
        source_label=item.source_label,
        poster_asset_key=item.poster_asset_key,
        autoplay=item.autoplay,
        muted=item.muted,
        looping=item.looping,
        priority=item.priority,
    )

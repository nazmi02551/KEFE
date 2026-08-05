from __future__ import annotations

from uuid import UUID

from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.case_media.models import (
    CaseMediaProjection,
    MediaAsset,
    MediaAssetWriteResult,
    MediaAuditEntry,
    MediaBindingWriteResult,
    MediaKind,
    MediaSlot,
    MediaState,
)
from kefe_api.modules.case_media.service import CaseMediaService


class SecuredCaseMediaService:
    def __init__(
        self,
        *,
        media: CaseMediaService,
        security: AdminSecurityService,
    ) -> None:
        self._media = media
        self._security = security

    def list_assets(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        offset: int,
        state: MediaState | None,
    ) -> tuple[MediaAsset, ...]:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_READ)
        return self._media.list_assets(limit=limit, offset=offset, state=state)

    def get_asset(self, principal: AdminPrincipal, media_asset_id: UUID) -> MediaAsset:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_READ)
        return self._media.get_asset(media_asset_id)

    def list_audit(
        self,
        principal: AdminPrincipal,
        media_asset_id: UUID,
    ) -> tuple[MediaAuditEntry, ...]:
        self._security.authorize(principal, AdminCapability.AUDIT_READ)
        return self._media.list_audit(media_asset_id)

    def register(
        self,
        principal: AdminPrincipal,
        *,
        asset_key: str,
        kind: MediaKind,
        delivery_ref: str,
        content_hash: str,
        byte_length: int,
        media_type: str,
        title: str,
        alt_text: str,
        caption: str | None,
        credit_label: str,
        source_label: str,
        poster_asset_key: str | None,
    ) -> MediaAssetWriteResult:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_MANAGE)
        return self._media.register(
            actor_ref=principal.audit_actor_ref,
            asset_key=asset_key,
            kind=kind,
            delivery_ref=delivery_ref,
            content_hash=content_hash,
            byte_length=byte_length,
            media_type=media_type,
            title=title,
            alt_text=alt_text,
            caption=caption,
            credit_label=credit_label,
            source_label=source_label,
            poster_asset_key=poster_asset_key,
        )

    def mark_ready(
        self,
        principal: AdminPrincipal,
        media_asset_id: UUID,
    ) -> MediaAssetWriteResult:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_MANAGE)
        return self._media.mark_ready(
            media_asset_id=media_asset_id,
            actor_ref=principal.audit_actor_ref,
        )

    def retire(
        self,
        principal: AdminPrincipal,
        media_asset_id: UUID,
    ) -> MediaAssetWriteResult:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_MANAGE)
        return self._media.retire(
            media_asset_id=media_asset_id,
            actor_ref=principal.audit_actor_ref,
        )

    def bind(
        self,
        principal: AdminPrincipal,
        *,
        case_version_id: UUID,
        media_asset_id: UUID,
        slot: MediaSlot,
        priority: int,
        autoplay: bool,
        muted: bool,
        looping: bool,
    ) -> MediaBindingWriteResult:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_MANAGE)
        return self._media.bind(
            case_version_id=case_version_id,
            media_asset_id=media_asset_id,
            slot=slot,
            priority=priority,
            autoplay=autoplay,
            muted=muted,
            looping=looping,
            actor_ref=principal.audit_actor_ref,
        )

    def project(
        self,
        principal: AdminPrincipal,
        case_version_id: UUID,
    ) -> tuple[CaseMediaProjection, ...]:
        self._security.authorize(principal, AdminCapability.MEDIA_ASSET_READ)
        return self._media.project(case_version_id)

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.case_media.models import (
    MediaAsset,
    MediaAuditEntry,
    MediaBinding,
    MediaSlot,
    MediaState,
)


class CaseMediaRepository(Protocol):
    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        state: MediaState | None = None,
    ) -> tuple[MediaAsset, ...]: ...

    def get_asset(self, media_asset_id: UUID) -> MediaAsset | None: ...

    def get_asset_by_key(self, asset_key: str) -> MediaAsset | None: ...

    def find_asset_conflict(
        self,
        *,
        delivery_ref: str,
        content_hash: str,
    ) -> MediaAsset | None: ...

    def insert_asset(
        self,
        *,
        asset: MediaAsset,
        audit: MediaAuditEntry,
    ) -> None: ...

    def transition_asset(
        self,
        *,
        media_asset_id: UUID,
        expected_state: MediaState,
        new_state: MediaState,
        audit: MediaAuditEntry,
    ) -> MediaAsset | None: ...

    def get_binding(
        self,
        *,
        case_version_id: UUID,
        slot: MediaSlot,
        media_asset_id: UUID,
    ) -> MediaBinding | None: ...

    def insert_binding(self, binding: MediaBinding) -> None: ...

    def list_bindings(self, case_version_id: UUID) -> tuple[MediaBinding, ...]: ...

    def list_audit(self, media_asset_id: UUID) -> tuple[MediaAuditEntry, ...]: ...

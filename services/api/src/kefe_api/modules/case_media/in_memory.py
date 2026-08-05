from __future__ import annotations

from dataclasses import replace
from threading import RLock
from uuid import UUID

from kefe_api.modules.case_media.models import (
    MediaAsset,
    MediaAuditEntry,
    MediaBinding,
    MediaKind,
    MediaSlot,
    MediaState,
)


class InMemoryCaseMediaRepository:
    def __init__(self) -> None:
        self._assets: dict[UUID, MediaAsset] = {}
        self._asset_keys: dict[str, UUID] = {}
        self._delivery_refs: dict[str, UUID] = {}
        self._content_hashes: dict[str, UUID] = {}
        self._bindings: dict[tuple[UUID, MediaSlot, UUID], MediaBinding] = {}
        self._audit: dict[UUID, list[MediaAuditEntry]] = {}
        self._lock = RLock()

    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        state: MediaState | None = None,
    ) -> tuple[MediaAsset, ...]:
        with self._lock:
            items = [
                asset for asset in self._assets.values() if state is None or asset.state is state
            ]
            items.sort(
                key=lambda item: (item.registered_at, item.media_asset_id),
                reverse=True,
            )
            return tuple(items[offset : offset + limit])

    def get_asset(self, media_asset_id: UUID) -> MediaAsset | None:
        with self._lock:
            return self._assets.get(media_asset_id)

    def get_asset_by_key(self, asset_key: str) -> MediaAsset | None:
        with self._lock:
            identity = self._asset_keys.get(asset_key)
            return self._assets.get(identity) if identity else None

    def find_asset_conflict(
        self,
        *,
        delivery_ref: str,
        content_hash: str,
    ) -> MediaAsset | None:
        with self._lock:
            identity = self._delivery_refs.get(delivery_ref) or self._content_hashes.get(
                content_hash
            )
            return self._assets.get(identity) if identity else None

    def insert_asset(
        self,
        *,
        asset: MediaAsset,
        audit: MediaAuditEntry,
    ) -> None:
        with self._lock:
            if (
                asset.media_asset_id in self._assets
                or asset.asset_key in self._asset_keys
                or asset.delivery_ref in self._delivery_refs
                or asset.content_hash in self._content_hashes
            ):
                raise ValueError("media asset conflict")
            self._assets[asset.media_asset_id] = asset
            self._asset_keys[asset.asset_key] = asset.media_asset_id
            self._delivery_refs[asset.delivery_ref] = asset.media_asset_id
            self._content_hashes[asset.content_hash] = asset.media_asset_id
            self._audit[asset.media_asset_id] = [audit]

    def transition_asset(
        self,
        *,
        media_asset_id: UUID,
        expected_state: MediaState,
        new_state: MediaState,
        audit: MediaAuditEntry,
    ) -> MediaAsset | None:
        with self._lock:
            asset = self._assets.get(media_asset_id)
            if asset is None or asset.state is not expected_state:
                return None
            updated = replace(asset, state=new_state)
            self._assets[media_asset_id] = updated
            self._audit.setdefault(media_asset_id, []).append(audit)
            return updated

    def get_binding(
        self,
        *,
        case_version_id: UUID,
        slot: MediaSlot,
        media_asset_id: UUID,
    ) -> MediaBinding | None:
        with self._lock:
            return self._bindings.get((case_version_id, slot, media_asset_id))

    def insert_binding(self, binding: MediaBinding) -> None:
        with self._lock:
            asset = self._assets.get(binding.media_asset_id)
            if asset is None or asset.state is not MediaState.READY:
                raise ValueError("media asset is not READY")
            if binding.autoplay:
                raise ValueError("media autoplay is forbidden")
            if asset.kind is MediaKind.IMAGE and (binding.muted or binding.looping):
                raise ValueError("image presentation flags are invalid")
            key = (binding.case_version_id, binding.slot, binding.media_asset_id)
            if key in self._bindings:
                raise ValueError("media binding conflict")
            self._bindings[key] = binding

    def list_bindings(self, case_version_id: UUID) -> tuple[MediaBinding, ...]:
        with self._lock:
            return tuple(
                binding
                for binding in self._bindings.values()
                if binding.case_version_id == case_version_id
            )

    def list_audit(self, media_asset_id: UUID) -> tuple[MediaAuditEntry, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._audit.get(media_asset_id, ()),
                    key=lambda item: (item.occurred_at, item.audit_id),
                )
            )

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
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
from kefe_api.modules.case_media.ports import CaseMediaDeliveryGate, CaseMediaRepository
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository

_ASSET_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
_DELIVERY_REF = re.compile(r"^media-ref:[a-z0-9][a-z0-9._:/-]{2,509}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_MEDIA_TYPES = {
    MediaKind.IMAGE: frozenset({"image/avif", "image/jpeg", "image/png", "image/webp"}),
    MediaKind.VIDEO: frozenset({"video/mp4", "video/webm"}),
}


class CaseMediaService:
    def __init__(
        self,
        *,
        repository: CaseMediaRepository,
        authoring: ContentAuthoringRepository,
        delivery_gate: CaseMediaDeliveryGate,
    ) -> None:
        self._repository = repository
        self._authoring = authoring
        self._delivery_gate = delivery_gate

    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        state: MediaState | None = None,
    ) -> tuple[MediaAsset, ...]:
        if not 1 <= limit <= 100:
            raise DomainError(
                "CASE_MEDIA_LIMIT_INVALID",
                "Media limit must be between 1 and 100",
                400,
            )
        if offset < 0:
            raise DomainError(
                "CASE_MEDIA_OFFSET_INVALID",
                "Media offset must not be negative",
                400,
            )
        return self._repository.list_assets(limit=limit, offset=offset, state=state)

    def get_asset(self, media_asset_id: UUID) -> MediaAsset:
        asset = self._repository.get_asset(media_asset_id)
        if asset is None:
            raise DomainError(
                "CASE_MEDIA_ASSET_NOT_FOUND",
                "Media asset was not found",
                404,
            )
        return asset

    def register(
        self,
        *,
        actor_ref: str,
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
        now: datetime | None = None,
    ) -> MediaAssetWriteResult:
        values = self._validated_registration(
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
        existing = self._repository.get_asset_by_key(values["asset_key"])
        if existing is not None:
            if self._registration_equal(existing, values):
                return MediaAssetWriteResult(asset=existing, replayed=True)
            raise DomainError(
                "CASE_MEDIA_ASSET_CONFLICT",
                "Media asset key conflicts with immutable metadata",
                409,
            )
        conflict = self._repository.find_asset_conflict(
            delivery_ref=values["delivery_ref"],
            content_hash=values["content_hash"],
        )
        if conflict is not None:
            raise DomainError(
                "CASE_MEDIA_ASSET_CONFLICT",
                "Media delivery reference or hash conflicts",
                409,
            )
        occurred_at = now or datetime.now(UTC)
        asset = MediaAsset(
            media_asset_id=uuid4(),
            state=MediaState.REGISTERED,
            registered_by=self._text(actor_ref, "actor_ref", 255),
            registered_at=occurred_at,
            **values,
        )
        audit = MediaAuditEntry(
            audit_id=uuid4(),
            media_asset_id=asset.media_asset_id,
            actor_ref=asset.registered_by,
            command="REGISTER",
            previous_state=None,
            new_state=MediaState.REGISTERED,
            occurred_at=occurred_at,
        )
        self._repository.insert_asset(asset=asset, audit=audit)
        return MediaAssetWriteResult(asset=asset, replayed=False)

    def mark_ready(
        self,
        *,
        media_asset_id: UUID,
        actor_ref: str,
        now: datetime | None = None,
    ) -> MediaAssetWriteResult:
        asset = self.get_asset(media_asset_id)
        if asset.state is MediaState.READY:
            return MediaAssetWriteResult(asset=asset, replayed=True)
        if asset.state is not MediaState.REGISTERED:
            raise DomainError(
                "CASE_MEDIA_STATE_INVALID",
                "Only REGISTERED media may become READY",
                409,
            )
        return MediaAssetWriteResult(
            asset=self._transition(
                asset=asset,
                actor_ref=actor_ref,
                command="MARK_READY",
                new_state=MediaState.READY,
                now=now,
            ),
            replayed=False,
        )

    def retire(
        self,
        *,
        media_asset_id: UUID,
        actor_ref: str,
        now: datetime | None = None,
    ) -> MediaAssetWriteResult:
        asset = self.get_asset(media_asset_id)
        if asset.state is MediaState.RETIRED:
            return MediaAssetWriteResult(asset=asset, replayed=True)
        return MediaAssetWriteResult(
            asset=self._transition(
                asset=asset,
                actor_ref=actor_ref,
                command="RETIRE",
                new_state=MediaState.RETIRED,
                now=now,
            ),
            replayed=False,
        )

    def bind(
        self,
        *,
        case_version_id: UUID,
        media_asset_id: UUID,
        slot: MediaSlot,
        priority: int,
        autoplay: bool,
        muted: bool,
        looping: bool,
        actor_ref: str,
        now: datetime | None = None,
    ) -> MediaBindingWriteResult:
        if self._authoring.get_version(case_version_id) is None:
            raise DomainError(
                "CASE_MEDIA_CASE_VERSION_NOT_FOUND",
                "CaseVersion was not found",
                404,
            )
        asset = self.get_asset(media_asset_id)
        if asset.state is not MediaState.READY:
            raise DomainError(
                "CASE_MEDIA_STATE_INVALID",
                "Only READY media may be bound",
                409,
            )
        if not 1 <= priority <= 1_000_000:
            raise DomainError(
                "CASE_MEDIA_PRIORITY_INVALID",
                "Media priority is invalid",
                400,
            )
        if autoplay:
            raise DomainError(
                "CASE_MEDIA_PRESENTATION_INVALID",
                "Video autoplay is forbidden",
                400,
            )
        if asset.kind is MediaKind.IMAGE and (muted or looping):
            raise DomainError(
                "CASE_MEDIA_PRESENTATION_INVALID",
                "Image media cannot be muted or looped",
                400,
            )
        existing = self._repository.get_binding(
            case_version_id=case_version_id,
            slot=slot,
            media_asset_id=media_asset_id,
        )
        if existing is not None:
            expected = (priority, autoplay, muted, looping)
            actual = (
                existing.priority,
                existing.autoplay,
                existing.muted,
                existing.looping,
            )
            if actual == expected:
                return MediaBindingWriteResult(binding=existing, replayed=True)
            raise DomainError(
                "CASE_MEDIA_BINDING_CONFLICT",
                "Media binding conflicts with immutable history",
                409,
            )
        binding = MediaBinding(
            binding_id=uuid4(),
            case_version_id=case_version_id,
            media_asset_id=media_asset_id,
            slot=slot,
            priority=priority,
            autoplay=autoplay,
            muted=muted,
            looping=looping,
            bound_by=self._text(actor_ref, "actor_ref", 255),
            bound_at=now or datetime.now(UTC),
        )
        try:
            self._repository.insert_binding(binding)
        except ValueError as exc:
            concurrent = self._repository.get_binding(
                case_version_id=case_version_id,
                slot=slot,
                media_asset_id=media_asset_id,
            )
            if concurrent is not None:
                actual = (
                    concurrent.priority,
                    concurrent.autoplay,
                    concurrent.muted,
                    concurrent.looping,
                )
                if actual == (priority, autoplay, muted, looping):
                    return MediaBindingWriteResult(binding=concurrent, replayed=True)
            latest = self._repository.get_asset(media_asset_id)
            if latest is None or latest.state is not MediaState.READY:
                raise DomainError(
                    "CASE_MEDIA_STATE_CONFLICT",
                    "Media state changed before binding",
                    409,
                ) from exc
            raise DomainError(
                "CASE_MEDIA_BINDING_CONFLICT",
                "Media binding conflicts with immutable history",
                409,
            ) from exc
        return MediaBindingWriteResult(binding=binding, replayed=False)

    def list_audit(self, media_asset_id: UUID) -> tuple[MediaAuditEntry, ...]:
        self.get_asset(media_asset_id)
        return self._repository.list_audit(media_asset_id)

    def project(self, case_version_id: UUID) -> tuple[CaseMediaProjection, ...]:
        if self._authoring.get_version(case_version_id) is None:
            raise DomainError(
                "CASE_MEDIA_CASE_VERSION_NOT_FOUND",
                "CaseVersion was not found",
                404,
            )
        items: list[CaseMediaProjection] = []
        for binding in self._repository.list_bindings(case_version_id):
            asset = self._repository.get_asset(binding.media_asset_id)
            if asset is None or asset.state is not MediaState.READY:
                continue
            if not self._delivery_gate.permits(asset.delivery_ref):
                continue
            items.append(
                CaseMediaProjection(
                    asset_key=asset.asset_key,
                    kind=asset.kind,
                    slot=binding.slot,
                    delivery_ref=asset.delivery_ref,
                    title=asset.title,
                    alt_text=asset.alt_text,
                    caption=asset.caption,
                    credit_label=asset.credit_label,
                    source_label=asset.source_label,
                    poster_asset_key=asset.poster_asset_key,
                    autoplay=binding.autoplay,
                    muted=binding.muted,
                    looping=binding.looping,
                    priority=binding.priority,
                )
            )
        return tuple(sorted(items, key=lambda item: (-item.priority, item.asset_key)))

    def _transition(
        self,
        *,
        asset: MediaAsset,
        actor_ref: str,
        command: str,
        new_state: MediaState,
        now: datetime | None,
    ) -> MediaAsset:
        occurred_at = now or datetime.now(UTC)
        audit = MediaAuditEntry(
            audit_id=uuid4(),
            media_asset_id=asset.media_asset_id,
            actor_ref=self._text(actor_ref, "actor_ref", 255),
            command=command,
            previous_state=asset.state,
            new_state=new_state,
            occurred_at=occurred_at,
        )
        updated = self._repository.transition_asset(
            media_asset_id=asset.media_asset_id,
            expected_state=asset.state,
            new_state=new_state,
            audit=audit,
        )
        if updated is None:
            raise DomainError(
                "CASE_MEDIA_STATE_CONFLICT",
                "Media state changed concurrently",
                409,
            )
        return updated

    def _validated_registration(self, **raw: object) -> dict[str, object]:
        asset_key = self._text(raw["asset_key"], "asset_key", 128)
        delivery_ref = self._text(raw["delivery_ref"], "delivery_ref", 512)
        content_hash = self._text(raw["content_hash"], "content_hash", 64)
        kind = raw["kind"]
        media_type = self._text(raw["media_type"], "media_type", 100)
        if not _ASSET_KEY.fullmatch(asset_key):
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Media asset key is invalid",
                400,
            )
        if not _DELIVERY_REF.fullmatch(delivery_ref):
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Media delivery reference is invalid",
                400,
            )
        if not _HASH.fullmatch(content_hash):
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Media content hash is invalid",
                400,
            )
        if not isinstance(kind, MediaKind) or media_type not in _MEDIA_TYPES[kind]:
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Media kind and media type are incompatible",
                400,
            )
        byte_length = raw["byte_length"]
        if not isinstance(byte_length, int) or not 1 <= byte_length <= 1_073_741_824:
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Media byte length is invalid",
                400,
            )
        caption = self._optional_text(raw["caption"], "caption", 1000)
        poster = self._optional_text(raw["poster_asset_key"], "poster_asset_key", 128)
        if poster is not None and not _ASSET_KEY.fullmatch(poster):
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                "Poster asset key is invalid",
                400,
            )
        return {
            "asset_key": asset_key,
            "kind": kind,
            "delivery_ref": delivery_ref,
            "content_hash": content_hash,
            "byte_length": byte_length,
            "media_type": media_type,
            "title": self._text(raw["title"], "title", 200),
            "alt_text": self._text(raw["alt_text"], "alt_text", 500),
            "caption": caption,
            "credit_label": self._text(raw["credit_label"], "credit_label", 200),
            "source_label": self._text(raw["source_label"], "source_label", 300),
            "poster_asset_key": poster,
        }

    @staticmethod
    def _registration_equal(asset: MediaAsset, values: dict[str, object]) -> bool:
        return all(getattr(asset, key) == value for key, value in values.items())

    @staticmethod
    def _text(value: object, field: str, maximum: int) -> str:
        if not isinstance(value, str):
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                f"{field} must be text",
                400,
            )
        normalized = value.strip()
        if not normalized or len(normalized) > maximum:
            raise DomainError(
                "CASE_MEDIA_ASSET_INVALID",
                f"{field} is invalid",
                400,
            )
        return normalized

    @classmethod
    def _optional_text(
        cls,
        value: object,
        field: str,
        maximum: int,
    ) -> str | None:
        if value is None:
            return None
        return cls._text(value, field, maximum)

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.modules.case_media.models import (
    MediaAsset,
    MediaAuditEntry,
    MediaBinding,
    MediaKind,
    MediaSlot,
    MediaState,
)


class PostgresCaseMediaRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        state: MediaState | None = None,
    ) -> tuple[MediaAsset, ...]:
        where = "" if state is None else "WHERE state = :state"
        params: dict[str, object] = {"limit": limit, "offset": offset}
        if state is not None:
            params["state"] = state.value
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        f"""
                    SELECT media_asset_id, asset_key, kind, delivery_ref, content_hash,
                           byte_length, media_type, title, alt_text, caption,
                           credit_label, source_label, poster_asset_key, state,
                           registered_by, registered_at
                    FROM media.asset
                    {where}
                    ORDER BY registered_at DESC, media_asset_id DESC
                    LIMIT :limit OFFSET :offset
                    """
                    ),
                    params,
                )
                .mappings()
                .all()
            )
        return tuple(self._asset(row) for row in rows)

    def get_asset(self, media_asset_id: UUID) -> MediaAsset | None:
        return self._get_asset("media_asset_id = :value", media_asset_id)

    def get_asset_by_key(self, asset_key: str) -> MediaAsset | None:
        return self._get_asset("asset_key = :value", asset_key)

    def _get_asset(self, predicate: str, value: object) -> MediaAsset | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                    SELECT media_asset_id, asset_key, kind, delivery_ref, content_hash,
                           byte_length, media_type, title, alt_text, caption,
                           credit_label, source_label, poster_asset_key, state,
                           registered_by, registered_at
                    FROM media.asset
                    WHERE {predicate}
                    """
                    ),
                    {"value": value},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._asset(row)

    def find_asset_conflict(
        self,
        *,
        delivery_ref: str,
        content_hash: str,
    ) -> MediaAsset | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT media_asset_id, asset_key, kind, delivery_ref, content_hash,
                           byte_length, media_type, title, alt_text, caption,
                           credit_label, source_label, poster_asset_key, state,
                           registered_by, registered_at
                    FROM media.asset
                    WHERE delivery_ref = :delivery_ref OR content_hash = :content_hash
                    ORDER BY registered_at, media_asset_id
                    LIMIT 1
                    """
                    ),
                    {"delivery_ref": delivery_ref, "content_hash": content_hash},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._asset(row)

    def insert_asset(
        self,
        *,
        asset: MediaAsset,
        audit: MediaAuditEntry,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO media.asset (
                        media_asset_id, asset_key, kind, delivery_ref, content_hash,
                        byte_length, media_type, title, alt_text, caption,
                        credit_label, source_label, poster_asset_key, state,
                        registered_by, registered_at
                    ) VALUES (
                        :media_asset_id, :asset_key, :kind, :delivery_ref, :content_hash,
                        :byte_length, :media_type, :title, :alt_text, :caption,
                        :credit_label, :source_label, :poster_asset_key, :state,
                        :registered_by, :registered_at
                    )
                    """
                ),
                self._asset_params(asset),
            )
            self._insert_audit(connection, audit)

    def transition_asset(
        self,
        *,
        media_asset_id: UUID,
        expected_state: MediaState,
        new_state: MediaState,
        audit: MediaAuditEntry,
    ) -> MediaAsset | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    UPDATE media.asset
                    SET state = :new_state
                    WHERE media_asset_id = :media_asset_id
                      AND state = :expected_state
                    RETURNING media_asset_id, asset_key, kind, delivery_ref, content_hash,
                              byte_length, media_type, title, alt_text, caption,
                              credit_label, source_label, poster_asset_key, state,
                              registered_by, registered_at
                    """
                    ),
                    {
                        "media_asset_id": media_asset_id,
                        "expected_state": expected_state.value,
                        "new_state": new_state.value,
                    },
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            self._insert_audit(connection, audit)
        return self._asset(row)

    def get_binding(
        self,
        *,
        case_version_id: UUID,
        slot: MediaSlot,
        media_asset_id: UUID,
    ) -> MediaBinding | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT binding_id, case_version_id, media_asset_id, slot, priority,
                           autoplay, muted, looping, bound_by, bound_at
                    FROM media.case_version_binding
                    WHERE case_version_id = :case_version_id
                      AND slot = :slot
                      AND media_asset_id = :media_asset_id
                    """
                    ),
                    {
                        "case_version_id": case_version_id,
                        "slot": slot.value,
                        "media_asset_id": media_asset_id,
                    },
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._binding(row)

    def insert_binding(self, binding: MediaBinding) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO media.case_version_binding (
                            binding_id, case_version_id, media_asset_id, slot, priority,
                            autoplay, muted, looping, bound_by, bound_at
                        ) VALUES (
                            :binding_id, :case_version_id, :media_asset_id, :slot, :priority,
                            :autoplay, :muted, :looping, :bound_by, :bound_at
                        )
                        """
                    ),
                    {
                        "binding_id": binding.binding_id,
                        "case_version_id": binding.case_version_id,
                        "media_asset_id": binding.media_asset_id,
                        "slot": binding.slot.value,
                        "priority": binding.priority,
                        "autoplay": binding.autoplay,
                        "muted": binding.muted,
                        "looping": binding.looping,
                        "bound_by": binding.bound_by,
                        "bound_at": binding.bound_at,
                    },
                )
        except DBAPIError as exc:
            raise ValueError("media binding conflict") from exc

    def list_bindings(self, case_version_id: UUID) -> tuple[MediaBinding, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT binding_id, case_version_id, media_asset_id, slot, priority,
                           autoplay, muted, looping, bound_by, bound_at
                    FROM media.case_version_binding
                    WHERE case_version_id = :case_version_id
                    ORDER BY priority DESC, binding_id
                    """
                    ),
                    {"case_version_id": case_version_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._binding(row) for row in rows)

    def list_audit(self, media_asset_id: UUID) -> tuple[MediaAuditEntry, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT audit_id, media_asset_id, actor_ref, command,
                           previous_state, new_state, occurred_at
                    FROM media.asset_audit
                    WHERE media_asset_id = :media_asset_id
                    ORDER BY occurred_at, audit_id
                    """
                    ),
                    {"media_asset_id": media_asset_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._audit(row) for row in rows)

    @staticmethod
    def _insert_audit(connection: Connection, audit: MediaAuditEntry) -> None:
        connection.execute(
            text(
                """
                INSERT INTO media.asset_audit (
                    audit_id, media_asset_id, actor_ref, command,
                    previous_state, new_state, occurred_at
                ) VALUES (
                    :audit_id, :media_asset_id, :actor_ref, :command,
                    :previous_state, :new_state, :occurred_at
                )
                """
            ),
            {
                "audit_id": audit.audit_id,
                "media_asset_id": audit.media_asset_id,
                "actor_ref": audit.actor_ref,
                "command": audit.command,
                "previous_state": (
                    None if audit.previous_state is None else audit.previous_state.value
                ),
                "new_state": audit.new_state.value,
                "occurred_at": audit.occurred_at,
            },
        )

    @staticmethod
    def _asset_params(asset: MediaAsset) -> dict[str, object]:
        return {
            "media_asset_id": asset.media_asset_id,
            "asset_key": asset.asset_key,
            "kind": asset.kind.value,
            "delivery_ref": asset.delivery_ref,
            "content_hash": asset.content_hash,
            "byte_length": asset.byte_length,
            "media_type": asset.media_type,
            "title": asset.title,
            "alt_text": asset.alt_text,
            "caption": asset.caption,
            "credit_label": asset.credit_label,
            "source_label": asset.source_label,
            "poster_asset_key": asset.poster_asset_key,
            "state": asset.state.value,
            "registered_by": asset.registered_by,
            "registered_at": asset.registered_at,
        }

    @staticmethod
    def _asset(row: Mapping[str, object]) -> MediaAsset:
        return MediaAsset(
            media_asset_id=row["media_asset_id"],
            asset_key=str(row["asset_key"]),
            kind=MediaKind(str(row["kind"])),
            delivery_ref=str(row["delivery_ref"]),
            content_hash=str(row["content_hash"]),
            byte_length=int(row["byte_length"]),
            media_type=str(row["media_type"]),
            title=str(row["title"]),
            alt_text=str(row["alt_text"]),
            caption=None if row["caption"] is None else str(row["caption"]),
            credit_label=str(row["credit_label"]),
            source_label=str(row["source_label"]),
            poster_asset_key=(
                None if row["poster_asset_key"] is None else str(row["poster_asset_key"])
            ),
            state=MediaState(str(row["state"])),
            registered_by=str(row["registered_by"]),
            registered_at=row["registered_at"],
        )

    @staticmethod
    def _binding(row: Mapping[str, object]) -> MediaBinding:
        return MediaBinding(
            binding_id=row["binding_id"],
            case_version_id=row["case_version_id"],
            media_asset_id=row["media_asset_id"],
            slot=MediaSlot(str(row["slot"])),
            priority=int(row["priority"]),
            autoplay=bool(row["autoplay"]),
            muted=bool(row["muted"]),
            looping=bool(row["looping"]),
            bound_by=str(row["bound_by"]),
            bound_at=row["bound_at"],
        )

    @staticmethod
    def _audit(row: Mapping[str, object]) -> MediaAuditEntry:
        return MediaAuditEntry(
            audit_id=row["audit_id"],
            media_asset_id=row["media_asset_id"],
            actor_ref=str(row["actor_ref"]),
            command=str(row["command"]),
            previous_state=(
                None if row["previous_state"] is None else MediaState(str(row["previous_state"]))
            ),
            new_state=MediaState(str(row["new_state"])),
            occurred_at=row["occurred_at"],
        )

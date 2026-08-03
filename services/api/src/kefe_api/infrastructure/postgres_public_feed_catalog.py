from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.knowledge.public_feed_catalog import (
    PublicFeedCatalogAuditEntry,
    PublicFeedCatalogConflictError,
    PublicFeedCatalogEntry,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile


class PostgresPublicFeedCatalogRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def register(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_catalog
                        WHERE feed_code = :feed_code OR adapter_code = :adapter_code
                        FOR UPDATE
                        """
                    ),
                    {
                        "feed_code": entry.feed_code,
                        "adapter_code": entry.adapter_code,
                    },
                ).mappings().one_or_none()
                if row is not None:
                    existing = self._from_row(row)
                    if (
                        existing.feed_code == entry.feed_code
                        and existing.adapter_code == entry.adapter_code
                        and existing.definition == entry.definition
                        and existing.configuration_hash == entry.configuration_hash
                    ):
                        return existing
                    raise PublicFeedCatalogConflictError(entry.feed_code)
                self._insert_entry(connection, entry)
                self._insert_audit(connection, audit)
        except IntegrityError as exc:
            raise PublicFeedCatalogConflictError(entry.feed_code) from exc
        return entry

    def get(self, entry_id: UUID) -> PublicFeedCatalogEntry | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_catalog
                    WHERE id = :entry_id
                    """
                ),
                {"entry_id": entry_id},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def get_by_feed_code(self, feed_code: str) -> PublicFeedCatalogEntry | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_catalog
                    WHERE feed_code = :feed_code
                    """
                ),
                {"feed_code": feed_code},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def list_entries(self) -> tuple[PublicFeedCatalogEntry, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_catalog
                    ORDER BY feed_code, id
                    """
                )
            ).mappings().all()
        return tuple(self._from_row(row) for row in rows)

    def transition(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_catalog
                        WHERE id = :entry_id
                        FOR UPDATE
                        """
                    ),
                    {"entry_id": entry.id},
                ).mappings().one_or_none()
                if row is None:
                    raise KeyError(entry.id)
                current = self._from_row(row)
                if (
                    current.state is not audit.previous_state
                    or current.definition != entry.definition
                    or current.configuration_hash != entry.configuration_hash
                ):
                    raise PublicFeedCatalogConflictError(entry.feed_code)
                result = connection.execute(
                    text(
                        """
                        UPDATE knowledge.public_feed_catalog
                        SET lifecycle_state = :state,
                            approved_by = :approved_by,
                            approved_at = :approved_at,
                            retired_by = :retired_by,
                            retired_at = :retired_at,
                            retirement_rationale = :retirement_rationale
                        WHERE id = :entry_id
                          AND lifecycle_state = :previous_state
                        """
                    ),
                    {
                        "entry_id": entry.id,
                        "previous_state": audit.previous_state.value,
                        "state": entry.state.value,
                        "approved_by": entry.approved_by,
                        "approved_at": entry.approved_at,
                        "retired_by": entry.retired_by,
                        "retired_at": entry.retired_at,
                        "retirement_rationale": entry.retirement_rationale,
                    },
                )
                if result.rowcount != 1:
                    raise PublicFeedCatalogConflictError(entry.feed_code)
                self._insert_audit(connection, audit)
        except IntegrityError as exc:
            raise PublicFeedCatalogConflictError(entry.feed_code) from exc
        return entry

    def list_audit(
        self,
        entry_id: UUID | None = None,
    ) -> tuple[PublicFeedCatalogAuditEntry, ...]:
        query = """
            SELECT audit_id, catalog_entry_id, feed_code, actor_ref, command,
                   previous_state, new_state, rationale, occurred_at
            FROM knowledge.public_feed_catalog_audit
        """
        parameters: dict[str, object] = {}
        if entry_id is not None:
            query += " WHERE catalog_entry_id = :entry_id"
            parameters["entry_id"] = entry_id
        query += " ORDER BY audit_seq"
        with self._engine.connect() as connection:
            rows = connection.execute(text(query), parameters).mappings().all()
        return tuple(
            PublicFeedCatalogAuditEntry(
                audit_id=row["audit_id"],
                catalog_entry_id=row["catalog_entry_id"],
                feed_code=row["feed_code"],
                actor_ref=row["actor_ref"],
                command=row["command"],
                previous_state=(
                    PublicFeedCatalogState(row["previous_state"])
                    if row["previous_state"] is not None
                    else None
                ),
                new_state=PublicFeedCatalogState(row["new_state"]),
                rationale=row["rationale"],
                occurred_at=row["occurred_at"],
            )
            for row in rows
        )

    @staticmethod
    def _insert_entry(
        connection: Connection,
        entry: PublicFeedCatalogEntry,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO knowledge.public_feed_catalog (
                    id, feed_code, adapter_code, lifecycle_state, definition,
                    configuration_hash, registered_by, registered_at,
                    approved_by, approved_at, retired_by, retired_at,
                    retirement_rationale
                ) VALUES (
                    :id, :feed_code, :adapter_code, :state,
                    CAST(:definition AS jsonb), :configuration_hash,
                    :registered_by, :registered_at, :approved_by, :approved_at,
                    :retired_by, :retired_at, :retirement_rationale
                )
                """
            ),
            {
                "id": entry.id,
                "feed_code": entry.feed_code,
                "adapter_code": entry.adapter_code,
                "state": entry.state.value,
                "definition": json.dumps(_definition_document(entry.definition)),
                "configuration_hash": entry.configuration_hash,
                "registered_by": entry.registered_by,
                "registered_at": entry.registered_at,
                "approved_by": entry.approved_by,
                "approved_at": entry.approved_at,
                "retired_by": entry.retired_by,
                "retired_at": entry.retired_at,
                "retirement_rationale": entry.retirement_rationale,
            },
        )

    @staticmethod
    def _insert_audit(
        connection: Connection,
        audit: PublicFeedCatalogAuditEntry,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO knowledge.public_feed_catalog_audit (
                    audit_id, catalog_entry_id, feed_code, actor_ref, command,
                    previous_state, new_state, rationale, occurred_at
                ) VALUES (
                    :audit_id, :catalog_entry_id, :feed_code, :actor_ref,
                    :command, :previous_state, :new_state, :rationale, :occurred_at
                )
                """
            ),
            {
                "audit_id": audit.audit_id,
                "catalog_entry_id": audit.catalog_entry_id,
                "feed_code": audit.feed_code,
                "actor_ref": audit.actor_ref,
                "command": audit.command,
                "previous_state": (
                    audit.previous_state.value
                    if audit.previous_state is not None
                    else None
                ),
                "new_state": audit.new_state.value,
                "rationale": audit.rationale,
                "occurred_at": audit.occurred_at,
            },
        )

    @staticmethod
    def _from_row(row) -> PublicFeedCatalogEntry:
        document = row["definition"]
        if isinstance(document, str):
            document = json.loads(document)
        return PublicFeedCatalogEntry(
            id=row["id"],
            definition=_definition_from_document(document),
            configuration_hash=row["configuration_hash"],
            state=PublicFeedCatalogState(row["lifecycle_state"]),
            registered_by=row["registered_by"],
            registered_at=row["registered_at"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            retired_by=row["retired_by"],
            retired_at=row["retired_at"],
            retirement_rationale=row["retirement_rationale"],
        )


def _definition_document(definition: PublicFeedDefinition) -> dict[str, Any]:
    profile = definition.parser_profile
    return {
        "feed_code": definition.feed_code,
        "display_name": definition.display_name,
        "adapter_code": definition.adapter_code,
        "external_locator": definition.external_locator,
        "parser_profile": {
            "accepted_media_types": list(profile.accepted_media_types),
            "max_document_bytes": profile.max_document_bytes,
            "max_elements": profile.max_elements,
            "max_depth": profile.max_depth,
            "max_items": profile.max_items,
            "max_node_text_chars": profile.max_node_text_chars,
            "max_total_text_chars": profile.max_total_text_chars,
            "max_attributes_per_element": profile.max_attributes_per_element,
            "max_total_attribute_chars": profile.max_total_attribute_chars,
            "max_metadata_field_chars": profile.max_metadata_field_chars,
        },
        "connect_timeout_ms": definition.connect_timeout_ms,
        "read_timeout_ms": definition.read_timeout_ms,
        "total_timeout_ms": definition.total_timeout_ms,
        "max_response_bytes": definition.max_response_bytes,
        "max_redirect_hops": definition.max_redirect_hops,
        "terms_evidence_ref": definition.terms_evidence_ref,
        "rate_limit_evidence_ref": definition.rate_limit_evidence_ref,
        "quota_limit": definition.quota_limit,
        "quota_window_seconds": definition.quota_window_seconds,
        "failure_threshold": definition.failure_threshold,
        "circuit_open_seconds": definition.circuit_open_seconds,
        "permit_ttl_seconds": definition.permit_ttl_seconds,
        "language_code": definition.language_code,
        "jurisdiction_code": definition.jurisdiction_code,
    }


def _definition_from_document(document: dict[str, Any]) -> PublicFeedDefinition:
    profile = document["parser_profile"]
    return PublicFeedDefinition(
        feed_code=document["feed_code"],
        display_name=document["display_name"],
        adapter_code=document["adapter_code"],
        external_locator=document["external_locator"],
        parser_profile=StrictRssAtomParseProfile(
            accepted_media_types=tuple(profile["accepted_media_types"]),
            max_document_bytes=int(profile["max_document_bytes"]),
            max_elements=int(profile["max_elements"]),
            max_depth=int(profile["max_depth"]),
            max_items=int(profile["max_items"]),
            max_node_text_chars=int(profile["max_node_text_chars"]),
            max_total_text_chars=int(profile["max_total_text_chars"]),
            max_attributes_per_element=int(profile["max_attributes_per_element"]),
            max_total_attribute_chars=int(profile["max_total_attribute_chars"]),
            max_metadata_field_chars=int(profile["max_metadata_field_chars"]),
        ),
        connect_timeout_ms=int(document["connect_timeout_ms"]),
        read_timeout_ms=int(document["read_timeout_ms"]),
        total_timeout_ms=int(document["total_timeout_ms"]),
        max_response_bytes=int(document["max_response_bytes"]),
        max_redirect_hops=int(document["max_redirect_hops"]),
        terms_evidence_ref=document["terms_evidence_ref"],
        rate_limit_evidence_ref=document["rate_limit_evidence_ref"],
        quota_limit=int(document["quota_limit"]),
        quota_window_seconds=int(document["quota_window_seconds"]),
        failure_threshold=int(document["failure_threshold"]),
        circuit_open_seconds=int(document["circuit_open_seconds"]),
        permit_ttl_seconds=int(document["permit_ttl_seconds"]),
        language_code=document.get("language_code"),
        jurisdiction_code=document.get("jurisdiction_code"),
    )


__all__ = ["PostgresPublicFeedCatalogRepository"]

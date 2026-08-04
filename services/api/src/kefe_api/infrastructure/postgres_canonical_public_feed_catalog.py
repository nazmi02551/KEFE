from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedDefinition,
    PublicFeedActivationProjection,
    PublicFeedActivationState,
    PublicFeedAuditAction,
    PublicFeedAuditEvent,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile


class PostgresCanonicalPublicFeedCatalogRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_definition
                        WHERE (feed_code = :feed_code
                               AND definition_version = :definition_version)
                           OR adapter_code = :adapter_code
                        FOR UPDATE
                        """
                    ),
                    {
                        "feed_code": definition.feed_code,
                        "definition_version": definition.definition_version,
                        "adapter_code": definition.definition.adapter_code,
                    },
                ).mappings().one_or_none()
                if row is not None:
                    existing = _definition_from_row(row)
                    if existing == definition:
                        return existing
                    raise ValueError("public feed definition identity conflict")
                _insert_definition(connection, definition)
        except IntegrityError as exc:
            raise ValueError("public feed definition identity conflict") from exc
        return definition

    def replace_definition(
        self,
        definition: CanonicalPublicFeedDefinition,
    ) -> CanonicalPublicFeedDefinition:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_definition
                        WHERE id = :definition_id
                        FOR UPDATE
                        """
                    ),
                    {"definition_id": definition.id},
                ).mappings().one_or_none()
                if row is None:
                    raise KeyError(definition.id)
                current = _definition_from_row(row)
                if current == definition:
                    return current
                if (
                    current.id != definition.id
                    or current.feed_code != definition.feed_code
                    or current.definition_version != definition.definition_version
                    or current.definition != definition.definition
                    or current.interval_seconds != definition.interval_seconds
                    or current.max_dispatch_attempts
                    != definition.max_dispatch_attempts
                    or current.configuration_hash != definition.configuration_hash
                    or current.created_at != definition.created_at
                    or current.created_by_actor_ref
                    != definition.created_by_actor_ref
                ):
                    raise ValueError("immutable public feed definition drift")
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.public_feed_definition
                        SET lifecycle_state = :state,
                            preflighted_at = :preflighted_at,
                            preflighted_by_actor_ref = :preflighted_by_actor_ref,
                            approved_at = :approved_at,
                            approved_by_actor_ref = :approved_by_actor_ref,
                            retired_at = :retired_at,
                            retired_by_actor_ref = :retired_by_actor_ref
                        WHERE id = :definition_id
                        """
                    ),
                    {
                        "definition_id": definition.id,
                        "state": definition.state.value,
                        "preflighted_at": definition.preflighted_at,
                        "preflighted_by_actor_ref": (
                            definition.preflighted_by_actor_ref
                        ),
                        "approved_at": definition.approved_at,
                        "approved_by_actor_ref": definition.approved_by_actor_ref,
                        "retired_at": definition.retired_at,
                        "retired_by_actor_ref": definition.retired_by_actor_ref,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("public feed definition transition conflict") from exc
        return definition

    def get_definition(
        self,
        feed_code: str,
        definition_version: int,
    ) -> CanonicalPublicFeedDefinition | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_definition
                    WHERE feed_code = :feed_code
                      AND definition_version = :definition_version
                    """
                ),
                {
                    "feed_code": feed_code,
                    "definition_version": definition_version,
                },
            ).mappings().one_or_none()
        return _definition_from_row(row) if row is not None else None

    def get_latest(self, feed_code: str) -> CanonicalPublicFeedDefinition | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_definition
                    WHERE feed_code = :feed_code
                    ORDER BY definition_version DESC
                    LIMIT 1
                    """
                ),
                {"feed_code": feed_code},
            ).mappings().one_or_none()
        return _definition_from_row(row) if row is not None else None

    def list_definitions(self) -> tuple[CanonicalPublicFeedDefinition, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_definition
                    ORDER BY feed_code, definition_version
                    """
                )
            ).mappings().all()
        return tuple(_definition_from_row(row) for row in rows)

    def add_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_activation
                        WHERE feed_definition_id = :definition_id
                           OR adapter_code = :adapter_code
                           OR schedule_id = :schedule_id
                        FOR UPDATE
                        """
                    ),
                    {
                        "definition_id": activation.feed_definition_id,
                        "adapter_code": activation.adapter_code,
                        "schedule_id": activation.schedule_id,
                    },
                ).mappings().one_or_none()
                if row is not None:
                    existing = _activation_from_row(row)
                    if existing == activation:
                        return existing
                    raise ValueError("public feed activation identity conflict")
                connection.execute(
                    text(
                        """
                        INSERT INTO knowledge.public_feed_activation (
                            id, feed_definition_id, feed_code,
                            definition_version, configuration_hash,
                            adapter_code, schedule_id, lifecycle_state,
                            activated_at, activated_by_actor_ref,
                            updated_at, updated_by_actor_ref
                        ) VALUES (
                            :id, :feed_definition_id, :feed_code,
                            :definition_version, :configuration_hash,
                            :adapter_code, :schedule_id, :state,
                            :activated_at, :activated_by_actor_ref,
                            :updated_at, :updated_by_actor_ref
                        )
                        """
                    ),
                    _activation_parameters(activation),
                )
        except IntegrityError as exc:
            raise ValueError("public feed activation identity conflict") from exc
        return activation

    def replace_activation(
        self,
        activation: PublicFeedActivationProjection,
    ) -> PublicFeedActivationProjection:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.public_feed_activation
                        WHERE feed_definition_id = :definition_id
                        FOR UPDATE
                        """
                    ),
                    {"definition_id": activation.feed_definition_id},
                ).mappings().one_or_none()
                if row is None:
                    raise KeyError(activation.feed_definition_id)
                current = _activation_from_row(row)
                if current == activation:
                    return current
                if (
                    current.id != activation.id
                    or current.feed_definition_id
                    != activation.feed_definition_id
                    or current.feed_code != activation.feed_code
                    or current.definition_version
                    != activation.definition_version
                    or current.configuration_hash
                    != activation.configuration_hash
                    or current.adapter_code != activation.adapter_code
                    or current.schedule_id != activation.schedule_id
                    or current.activated_at != activation.activated_at
                    or current.activated_by_actor_ref
                    != activation.activated_by_actor_ref
                ):
                    raise ValueError("immutable activation projection drift")
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.public_feed_activation
                        SET lifecycle_state = :state,
                            updated_at = :updated_at,
                            updated_by_actor_ref = :updated_by_actor_ref
                        WHERE feed_definition_id = :feed_definition_id
                        """
                    ),
                    {
                        "feed_definition_id": activation.feed_definition_id,
                        "state": activation.state.value,
                        "updated_at": activation.updated_at,
                        "updated_by_actor_ref": activation.updated_by_actor_ref,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("public feed activation transition conflict") from exc
        return activation

    def get_activation_for_definition(
        self,
        definition_id: UUID,
    ) -> PublicFeedActivationProjection | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.public_feed_activation
                    WHERE feed_definition_id = :definition_id
                    """
                ),
                {"definition_id": definition_id},
            ).mappings().one_or_none()
        return _activation_from_row(row) if row is not None else None

    def append_audit(
        self,
        *,
        definition_id: UUID,
        activation_id: UUID | None,
        action: PublicFeedAuditAction,
        actor_ref: str,
        occurred_at,
        configuration_hash: str,
    ) -> PublicFeedAuditEvent:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO knowledge.public_feed_audit (
                        definition_id, activation_id, action, actor_ref,
                        occurred_at, configuration_hash
                    ) VALUES (
                        :definition_id, :activation_id, :action, :actor_ref,
                        :occurred_at, :configuration_hash
                    )
                    RETURNING sequence
                    """
                ),
                {
                    "definition_id": definition_id,
                    "activation_id": activation_id,
                    "action": action.value,
                    "actor_ref": actor_ref,
                    "occurred_at": occurred_at,
                    "configuration_hash": configuration_hash,
                },
            ).mappings().one()
        return PublicFeedAuditEvent(
            sequence=int(row["sequence"]),
            definition_id=definition_id,
            activation_id=activation_id,
            action=action,
            actor_ref=actor_ref,
            occurred_at=occurred_at,
            configuration_hash=configuration_hash,
        )

    def list_audit(self, definition_id: UUID) -> tuple[PublicFeedAuditEvent, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT sequence, definition_id, activation_id, action,
                           actor_ref, occurred_at, configuration_hash
                    FROM knowledge.public_feed_audit
                    WHERE definition_id = :definition_id
                    ORDER BY sequence
                    """
                ),
                {"definition_id": definition_id},
            ).mappings().all()
        return tuple(
            PublicFeedAuditEvent(
                sequence=int(row["sequence"]),
                definition_id=row["definition_id"],
                activation_id=row["activation_id"],
                action=PublicFeedAuditAction(row["action"]),
                actor_ref=row["actor_ref"],
                occurred_at=row["occurred_at"],
                configuration_hash=row["configuration_hash"],
            )
            for row in rows
        )


def _insert_definition(
    connection: Connection,
    definition: CanonicalPublicFeedDefinition,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO knowledge.public_feed_definition (
                id, feed_code, definition_version, adapter_code, definition,
                interval_seconds, max_dispatch_attempts, configuration_hash,
                lifecycle_state, created_at, created_by_actor_ref,
                preflighted_at, preflighted_by_actor_ref,
                approved_at, approved_by_actor_ref,
                retired_at, retired_by_actor_ref
            ) VALUES (
                :id, :feed_code, :definition_version, :adapter_code,
                CAST(:definition AS jsonb), :interval_seconds,
                :max_dispatch_attempts, :configuration_hash, :state,
                :created_at, :created_by_actor_ref,
                :preflighted_at, :preflighted_by_actor_ref,
                :approved_at, :approved_by_actor_ref,
                :retired_at, :retired_by_actor_ref
            )
            """
        ),
        {
            "id": definition.id,
            "feed_code": definition.feed_code,
            "definition_version": definition.definition_version,
            "adapter_code": definition.definition.adapter_code,
            "definition": json.dumps(_definition_document(definition.definition)),
            "interval_seconds": definition.interval_seconds,
            "max_dispatch_attempts": definition.max_dispatch_attempts,
            "configuration_hash": definition.configuration_hash,
            "state": definition.state.value,
            "created_at": definition.created_at,
            "created_by_actor_ref": definition.created_by_actor_ref,
            "preflighted_at": definition.preflighted_at,
            "preflighted_by_actor_ref": definition.preflighted_by_actor_ref,
            "approved_at": definition.approved_at,
            "approved_by_actor_ref": definition.approved_by_actor_ref,
            "retired_at": definition.retired_at,
            "retired_by_actor_ref": definition.retired_by_actor_ref,
        },
    )


def _activation_parameters(
    activation: PublicFeedActivationProjection,
) -> dict[str, object]:
    return {
        "id": activation.id,
        "feed_definition_id": activation.feed_definition_id,
        "feed_code": activation.feed_code,
        "definition_version": activation.definition_version,
        "configuration_hash": activation.configuration_hash,
        "adapter_code": activation.adapter_code,
        "schedule_id": activation.schedule_id,
        "state": activation.state.value,
        "activated_at": activation.activated_at,
        "activated_by_actor_ref": activation.activated_by_actor_ref,
        "updated_at": activation.updated_at,
        "updated_by_actor_ref": activation.updated_by_actor_ref,
    }


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


def _definition_from_row(row) -> CanonicalPublicFeedDefinition:
    document = row["definition"]
    if isinstance(document, str):
        document = json.loads(document)
    return CanonicalPublicFeedDefinition(
        id=row["id"],
        feed_code=row["feed_code"],
        definition_version=int(row["definition_version"]),
        definition=_definition_from_document(document),
        interval_seconds=int(row["interval_seconds"]),
        max_dispatch_attempts=int(row["max_dispatch_attempts"]),
        configuration_hash=row["configuration_hash"],
        state=PublicFeedCatalogState(row["lifecycle_state"]),
        created_at=row["created_at"],
        created_by_actor_ref=row["created_by_actor_ref"],
        preflighted_at=row["preflighted_at"],
        preflighted_by_actor_ref=row["preflighted_by_actor_ref"],
        approved_at=row["approved_at"],
        approved_by_actor_ref=row["approved_by_actor_ref"],
        retired_at=row["retired_at"],
        retired_by_actor_ref=row["retired_by_actor_ref"],
    )


def _activation_from_row(row) -> PublicFeedActivationProjection:
    return PublicFeedActivationProjection(
        id=row["id"],
        feed_definition_id=row["feed_definition_id"],
        feed_code=row["feed_code"],
        definition_version=int(row["definition_version"]),
        configuration_hash=row["configuration_hash"],
        adapter_code=row["adapter_code"],
        schedule_id=row["schedule_id"],
        state=PublicFeedActivationState(row["lifecycle_state"]),
        activated_at=row["activated_at"],
        activated_by_actor_ref=row["activated_by_actor_ref"],
        updated_at=row["updated_at"],
        updated_by_actor_ref=row["updated_by_actor_ref"],
    )


__all__ = ["PostgresCanonicalPublicFeedCatalogRepository"]

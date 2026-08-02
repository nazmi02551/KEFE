from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, text

from kefe_api.modules.knowledge.feed_activation import (
    FeedPipelineDefinition,
    FeedPipelineLifecycle,
)


class PostgresFeedPipelineDefinitionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get(
        self,
        definition: FeedPipelineDefinition,
    ) -> FeedPipelineDefinition:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO knowledge.feed_pipeline_definition (
                        feed_code,
                        adapter_code,
                        external_locator,
                        adoption_configuration_hash,
                        parser_configuration_hash,
                        extraction_pipeline_code,
                        extraction_pipeline_version,
                        acquisition_configuration_hash,
                        interval_seconds,
                        max_dispatch_attempts,
                        evidence_capability_ref,
                        lifecycle_state,
                        dependency_fingerprint,
                        verified_at,
                        created_at,
                        updated_at
                    ) VALUES (
                        :feed_code,
                        :adapter_code,
                        :external_locator,
                        :adoption_configuration_hash,
                        :parser_configuration_hash,
                        :extraction_pipeline_code,
                        :extraction_pipeline_version,
                        :acquisition_configuration_hash,
                        :interval_seconds,
                        :max_dispatch_attempts,
                        :evidence_capability_ref,
                        :lifecycle_state,
                        :dependency_fingerprint,
                        :verified_at,
                        :created_at,
                        :updated_at
                    )
                    ON CONFLICT (feed_code) DO NOTHING
                    """
                ),
                self._params(definition),
            )
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.feed_pipeline_definition
                    WHERE feed_code = :feed_code
                    """
                ),
                {"feed_code": definition.feed_code},
            ).mappings().one()
            stored = self._from_row(row)
            if stored.immutable_configuration != definition.immutable_configuration:
                raise ValueError("feed pipeline configuration is immutable")
            return stored

    def get(self, feed_code: str) -> FeedPipelineDefinition | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.feed_pipeline_definition
                    WHERE feed_code = :feed_code
                    """
                ),
                {"feed_code": feed_code},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def transition(
        self,
        *,
        feed_code: str,
        target: FeedPipelineLifecycle,
        at: datetime,
        dependency_fingerprint: str | None = None,
    ) -> FeedPipelineDefinition:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.feed_pipeline_definition
                    WHERE feed_code = :feed_code
                    FOR UPDATE
                    """
                ),
                {"feed_code": feed_code},
            ).mappings().one_or_none()
            if row is None:
                raise KeyError(feed_code)
            current = self._from_row(row)
            updated = current.transition(
                target,
                at=at,
                dependency_fingerprint=dependency_fingerprint,
            )
            connection.execute(
                text(
                    """
                    UPDATE knowledge.feed_pipeline_definition
                    SET lifecycle_state = :lifecycle_state,
                        dependency_fingerprint = :dependency_fingerprint,
                        verified_at = :verified_at,
                        updated_at = :updated_at
                    WHERE feed_code = :feed_code
                    """
                ),
                {
                    "feed_code": updated.feed_code,
                    "lifecycle_state": updated.lifecycle_state.value,
                    "dependency_fingerprint": updated.dependency_fingerprint,
                    "verified_at": updated.verified_at,
                    "updated_at": updated.updated_at,
                },
            )
            return updated

    @staticmethod
    def _params(definition: FeedPipelineDefinition) -> dict[str, object]:
        return {
            "feed_code": definition.feed_code,
            "adapter_code": definition.adapter_code,
            "external_locator": definition.external_locator,
            "adoption_configuration_hash": (
                definition.adoption_configuration_hash
            ),
            "parser_configuration_hash": definition.parser_configuration_hash,
            "extraction_pipeline_code": definition.extraction_pipeline_code,
            "extraction_pipeline_version": definition.extraction_pipeline_version,
            "acquisition_configuration_hash": (
                definition.acquisition_configuration_hash
            ),
            "interval_seconds": definition.interval_seconds,
            "max_dispatch_attempts": definition.max_dispatch_attempts,
            "evidence_capability_ref": definition.evidence_capability_ref,
            "lifecycle_state": definition.lifecycle_state.value,
            "dependency_fingerprint": definition.dependency_fingerprint,
            "verified_at": definition.verified_at,
            "created_at": definition.created_at,
            "updated_at": definition.updated_at,
        }

    @staticmethod
    def _from_row(row) -> FeedPipelineDefinition:
        return FeedPipelineDefinition(
            feed_code=row["feed_code"],
            adapter_code=row["adapter_code"],
            external_locator=row["external_locator"],
            adoption_configuration_hash=row["adoption_configuration_hash"],
            parser_configuration_hash=row["parser_configuration_hash"],
            extraction_pipeline_code=row["extraction_pipeline_code"],
            extraction_pipeline_version=row["extraction_pipeline_version"],
            acquisition_configuration_hash=row["acquisition_configuration_hash"],
            interval_seconds=row["interval_seconds"],
            max_dispatch_attempts=row["max_dispatch_attempts"],
            evidence_capability_ref=row["evidence_capability_ref"],
            lifecycle_state=FeedPipelineLifecycle(row["lifecycle_state"]),
            dependency_fingerprint=row["dependency_fingerprint"],
            verified_at=row["verified_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


__all__ = ["PostgresFeedPipelineDefinitionRepository"]

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.infrastructure.postgres_flow_pinned_content_authoring import (
    PostgresFlowPinnedContentAuthoringRepository,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    LifecycleAuditEntry,
)
from kefe_api.modules.editorial_projection.models import EditorialProjectionRecord


class PostgresEditorialProjectionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_idempotency(
        self,
        candidate_proposal_id: UUID,
        idempotency_key: str,
    ) -> EditorialProjectionRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, candidate_proposal_id, proposal_review_decision_id,
                           profile_code, profile_version, idempotency_key,
                           requested_by_admin_ref, input_hash, authoring_case_id,
                           authoring_case_version_id, created_at
                    FROM editorial.projection_record
                    WHERE candidate_proposal_id = :candidate_proposal_id
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "candidate_proposal_id": candidate_proposal_id,
                    "idempotency_key": idempotency_key,
                },
            ).mappings().one_or_none()
        return self._record(row) if row is not None else None

    def get_by_candidate(
        self,
        candidate_proposal_id: UUID,
    ) -> EditorialProjectionRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, candidate_proposal_id, proposal_review_decision_id,
                           profile_code, profile_version, idempotency_key,
                           requested_by_admin_ref, input_hash, authoring_case_id,
                           authoring_case_version_id, created_at
                    FROM editorial.projection_record
                    WHERE candidate_proposal_id = :candidate_proposal_id
                    """
                ),
                {"candidate_proposal_id": candidate_proposal_id},
            ).mappings().one_or_none()
        return self._record(row) if row is not None else None

    def create_atomically(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
        record: EditorialProjectionRecord,
    ) -> None:
        document = PostgresFlowPinnedContentAuthoringRepository._document(
            initial_version
        )
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.case_item (id, slug, created_at)
                        VALUES (:id, :slug, :created_at)
                        """
                    ),
                    {
                        "id": identity.id,
                        "slug": identity.slug,
                        "created_at": identity.created_at,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.case_version (
                            id, case_id, version_no, lifecycle_state, aggregate,
                            created_at, updated_at, published_at
                        ) VALUES (
                            :id, :case_id, :version_no, 'DRAFT',
                            CAST(:aggregate AS jsonb), :created_at, now(), NULL
                        )
                        """
                    ),
                    {
                        "id": initial_version.id,
                        "case_id": initial_version.case_id,
                        "version_no": initial_version.version_no,
                        "aggregate": json.dumps(document),
                        "created_at": initial_version.created_at,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.lifecycle_audit (
                            audit_id, case_id, case_version_id, actor_ref, command,
                            previous_state, new_state, rationale, occurred_at
                        ) VALUES (
                            :audit_id, :case_id, :case_version_id, :actor_ref,
                            :command, NULL, 'DRAFT', :rationale, :occurred_at
                        )
                        """
                    ),
                    {
                        "audit_id": audit.audit_id,
                        "case_id": audit.case_id,
                        "case_version_id": audit.case_version_id,
                        "actor_ref": audit.actor_ref,
                        "command": audit.command,
                        "rationale": audit.rationale,
                        "occurred_at": audit.occurred_at,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.projection_record (
                            id, candidate_proposal_id, proposal_review_decision_id,
                            profile_code, profile_version, idempotency_key,
                            requested_by_admin_ref, input_hash, authoring_case_id,
                            authoring_case_version_id, created_at
                        ) VALUES (
                            :id, :candidate_proposal_id,
                            :proposal_review_decision_id, :profile_code,
                            :profile_version, :idempotency_key,
                            :requested_by_admin_ref, :input_hash,
                            :authoring_case_id, :authoring_case_version_id,
                            :created_at
                        )
                        """
                    ),
                    {
                        "id": record.id,
                        "candidate_proposal_id": record.candidate_proposal_id,
                        "proposal_review_decision_id": (
                            record.proposal_review_decision_id
                        ),
                        "profile_code": record.profile_code,
                        "profile_version": record.profile_version,
                        "idempotency_key": record.idempotency_key,
                        "requested_by_admin_ref": record.requested_by_admin_ref,
                        "input_hash": record.input_hash,
                        "authoring_case_id": record.authoring_case_id,
                        "authoring_case_version_id": (
                            record.authoring_case_version_id
                        ),
                        "created_at": record.created_at,
                    },
                )
        except IntegrityError as exc:
            raise ValueError(
                "projection conflicts with existing authoring or lineage state"
            ) from exc

    @staticmethod
    def _record(row) -> EditorialProjectionRecord:
        return EditorialProjectionRecord(
            id=row["id"],
            candidate_proposal_id=row["candidate_proposal_id"],
            proposal_review_decision_id=row["proposal_review_decision_id"],
            profile_code=row["profile_code"],
            profile_version=row["profile_version"],
            idempotency_key=row["idempotency_key"],
            requested_by_admin_ref=row["requested_by_admin_ref"],
            input_hash=row["input_hash"],
            authoring_case_id=row["authoring_case_id"],
            authoring_case_version_id=row["authoring_case_version_id"],
            created_at=row["created_at"],
        )

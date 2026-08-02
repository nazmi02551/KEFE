from __future__ import annotations

from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueQuery,
    ProposalQueueRecord,
    ProposalQueueReviewState,
)

_QUEUE_SELECT = """
SELECT
    p.id,
    p.proposal_kind,
    p.payload_schema_ref,
    p.payload_schema_version,
    p.payload,
    p.payload_hash,
    p.run_id,
    p.stage_execution_id,
    p.taxonomy_version,
    p.configuration_version,
    p.methodology_version,
    p.confidence,
    p.risk_code,
    p.ai_execution_ref,
    p.provenance_ref,
    p.supersedes_proposal_id,
    p.created_at,
    ir.run_key AS queue_run_key,
    ir.source_artifact_id AS queue_source_artifact_id,
    ir.normalized_artifact_id AS queue_normalized_artifact_id,
    ir.input_content_hash AS queue_input_content_hash,
    ir.pipeline_code AS queue_pipeline_code,
    ir.pipeline_version AS queue_pipeline_version,
    ir.configuration_hash AS queue_configuration_hash,
    ir.taxonomy_version AS queue_run_taxonomy_version,
    ir.methodology_version AS queue_run_methodology_version,
    ir.locale AS queue_locale,
    ir.jurisdiction_code AS queue_jurisdiction_code,
    ir.state AS queue_run_state,
    ir.created_at AS queue_run_created_at,
    ir.updated_at AS queue_run_updated_at,
    rd.id AS queue_review_id,
    rd.decision AS queue_review_decision,
    rd.reviewer_ref AS queue_reviewer_ref,
    rd.decided_at AS queue_decided_at,
    rd.rationale AS queue_rationale,
    rd.reason_code AS queue_reason_code,
    rd.policy_version AS queue_policy_version,
    rd.risk_policy_version AS queue_risk_policy_version
FROM ingestion.proposal p
JOIN ingestion.ingestion_run ir ON ir.id = p.run_id
LEFT JOIN ingestion.proposal_review_decision rd ON rd.proposal_id = p.id
"""


class PostgresProposalReviewQueueRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_proposal_queue(
        self,
        query: ProposalQueueQuery,
    ) -> tuple[ProposalQueueRecord, ...]:
        clauses: list[str] = []
        params: dict[str, object] = {"limit": query.limit}
        if query.review_state is ProposalQueueReviewState.PENDING:
            clauses.append("rd.id IS NULL")
        elif query.review_state is not None:
            clauses.append("rd.decision = :review_state")
            params["review_state"] = query.review_state.value
        if query.proposal_kind is not None:
            clauses.append("p.proposal_kind = :proposal_kind")
            params["proposal_kind"] = query.proposal_kind
        if query.risk_code is not None:
            clauses.append("p.risk_code = :risk_code")
            params["risk_code"] = query.risk_code
        if query.run_id is not None:
            clauses.append("p.run_id = :run_id")
            params["run_id"] = query.run_id
        if query.pipeline_code is not None:
            clauses.append("ir.pipeline_code = :pipeline_code")
            params["pipeline_code"] = query.pipeline_code
        if query.after_created_at is not None:
            assert query.after_proposal_id is not None
            clauses.append(
                "(p.created_at, p.id) > (:after_created_at, :after_proposal_id)"
            )
            params["after_created_at"] = query.after_created_at
            params["after_proposal_id"] = query.after_proposal_id

        statement = _QUEUE_SELECT
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += " ORDER BY p.created_at ASC, p.id ASC LIMIT :limit"
        with self._engine.connect() as connection:
            rows = connection.execute(text(statement), params).mappings().all()
        return tuple(self._record_from_row(row) for row in rows)

    def get_proposal_queue_record(
        self,
        proposal_id: UUID,
    ) -> ProposalQueueRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(_QUEUE_SELECT + " WHERE p.id = :proposal_id"),
                {"proposal_id": proposal_id},
            ).mappings().one_or_none()
        return self._record_from_row(row) if row else None

    @classmethod
    def _record_from_row(cls, row) -> ProposalQueueRecord:
        return ProposalQueueRecord(
            proposal=Proposal(
                id=row["id"],
                proposal_kind=row["proposal_kind"],
                payload_schema_ref=row["payload_schema_ref"],
                payload_schema_version=row["payload_schema_version"],
                payload=dict(row["payload"]),
                payload_hash=row["payload_hash"],
                run_id=row["run_id"],
                stage_execution_id=row["stage_execution_id"],
                taxonomy_version=row["taxonomy_version"],
                configuration_version=row["configuration_version"],
                methodology_version=row["methodology_version"],
                confidence=row["confidence"],
                risk_code=row["risk_code"],
                ai_execution_ref=row["ai_execution_ref"],
                provenance_ref=row["provenance_ref"],
                supersedes_proposal_id=row["supersedes_proposal_id"],
                created_at=row["created_at"],
            ),
            run=cls._run_from_row(row),
            review=cls._review_from_row(row),
        )

    @staticmethod
    def _run_from_row(row) -> IngestionRun:
        source_id = row["queue_source_artifact_id"]
        normalized_id = row["queue_normalized_artifact_id"]
        return IngestionRun(
            id=row["run_id"],
            run_key=row["queue_run_key"],
            input_artifact_kind=(
                InputArtifactKind.SOURCE_ARTIFACT
                if source_id is not None
                else InputArtifactKind.NORMALIZED_ARTIFACT
            ),
            input_artifact_id=source_id if source_id is not None else normalized_id,
            input_content_hash=row["queue_input_content_hash"],
            pipeline_code=row["queue_pipeline_code"],
            pipeline_version=row["queue_pipeline_version"],
            configuration_hash=row["queue_configuration_hash"],
            taxonomy_version=row["queue_run_taxonomy_version"],
            methodology_version=row["queue_run_methodology_version"],
            locale=row["queue_locale"],
            jurisdiction_code=row["queue_jurisdiction_code"],
            state=IngestionRunState(row["queue_run_state"]),
            created_at=row["queue_run_created_at"],
            updated_at=row["queue_run_updated_at"],
        )

    @staticmethod
    def _review_from_row(row) -> ProposalReviewDecision | None:
        review_id = row["queue_review_id"]
        if review_id is None:
            return None
        return ProposalReviewDecision(
            id=review_id,
            proposal_id=row["id"],
            decision=ProposalReviewDecisionKind(row["queue_review_decision"]),
            reviewer_ref=row["queue_reviewer_ref"],
            decided_at=row["queue_decided_at"],
            rationale=row["queue_rationale"],
            reason_code=row["queue_reason_code"],
            policy_version=row["queue_policy_version"],
            risk_policy_version=row["queue_risk_policy_version"],
        )

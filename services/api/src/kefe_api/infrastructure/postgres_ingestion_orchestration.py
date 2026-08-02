from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
)


class PostgresIngestionOrchestrationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get_run(self, run: IngestionRun) -> IngestionRun:
        with self._engine.begin() as connection:
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO ingestion.ingestion_run (
                        id, run_key, input_artifact_kind, input_artifact_id,
                        input_content_hash, pipeline_code, pipeline_version,
                        configuration_hash, taxonomy_version, methodology_version,
                        locale, jurisdiction_code, state, created_at, updated_at
                    ) VALUES (
                        :id, :run_key, :input_artifact_kind, :input_artifact_id,
                        :input_content_hash, :pipeline_code, :pipeline_version,
                        :configuration_hash, :taxonomy_version, :methodology_version,
                        :locale, :jurisdiction_code, :state, :created_at, :updated_at
                    )
                    ON CONFLICT (run_key) DO NOTHING
                    RETURNING id
                    """
                ),
                self._run_params(run),
            ).scalar_one_or_none()
            if inserted is not None:
                return run
            row = connection.execute(
                text("SELECT * FROM ingestion.ingestion_run WHERE run_key = :run_key"),
                {"run_key": run.run_key},
            ).mappings().one()
        return self._run(row)

    def get_run(self, run_id: UUID) -> IngestionRun | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM ingestion.ingestion_run WHERE id = :run_id"),
                {"run_id": run_id},
            ).mappings().one_or_none()
        return self._run(row) if row is not None else None

    def update_run(self, run: IngestionRun) -> None:
        with self._engine.begin() as connection:
            current = connection.execute(
                text(
                    """
                    SELECT run_key FROM ingestion.ingestion_run
                    WHERE id = :run_id FOR UPDATE
                    """
                ),
                {"run_id": run.id},
            ).mappings().one_or_none()
            if current is None:
                raise KeyError(run.id)
            if current["run_key"] != run.run_key:
                raise ValueError("run_key is immutable")
            connection.execute(
                text(
                    """
                    UPDATE ingestion.ingestion_run
                    SET state = :state, updated_at = :updated_at
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run.id,
                    "state": run.state.value,
                    "updated_at": run.updated_at,
                },
            )

    def add_stage_execution(self, execution: StageExecution) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO ingestion.stage_execution (
                            id, run_id, stage_code, stage_version, attempt_no,
                            max_attempts, executor_kind, input_hash, output_hash,
                            started_at, completed_at, outcome, error_code,
                            execution_ref, trace_id
                        ) VALUES (
                            :id, :run_id, :stage_code, :stage_version, :attempt_no,
                            :max_attempts, :executor_kind, :input_hash, :output_hash,
                            :started_at, :completed_at, :outcome, :error_code,
                            :execution_ref, :trace_id
                        )
                        """
                    ),
                    {
                        "id": execution.id,
                        "run_id": execution.run_id,
                        "stage_code": execution.stage_code,
                        "stage_version": execution.stage_version,
                        "attempt_no": execution.attempt_no,
                        "max_attempts": execution.max_attempts,
                        "executor_kind": execution.executor_kind.value,
                        "input_hash": execution.input_hash,
                        "output_hash": execution.output_hash,
                        "started_at": execution.started_at,
                        "completed_at": execution.completed_at,
                        "outcome": execution.outcome.value,
                        "error_code": execution.error_code,
                        "execution_ref": execution.execution_ref,
                        "trace_id": execution.trace_id,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("stage execution conflicts with existing attempt") from exc

    def list_stage_executions(
        self,
        run_id: UUID,
        *,
        stage_code: str | None = None,
        stage_version: str | None = None,
    ) -> tuple[StageExecution, ...]:
        clauses = ["run_id = :run_id"]
        params: dict[str, object] = {"run_id": run_id}
        if stage_code is not None:
            clauses.append("stage_code = :stage_code")
            params["stage_code"] = stage_code
        if stage_version is not None:
            clauses.append("stage_version = :stage_version")
            params["stage_version"] = stage_version
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT * FROM ingestion.stage_execution WHERE "
                    + " AND ".join(clauses)
                    + " ORDER BY started_at, attempt_no, id"
                ),
                params,
            ).mappings().all()
        return tuple(self._stage(row) for row in rows)

    def add_proposal(self, proposal: Proposal) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO ingestion.proposal (
                            id, proposal_kind, payload_schema_ref,
                            payload_schema_version, payload, payload_hash,
                            run_id, stage_execution_id, taxonomy_version,
                            configuration_version, methodology_version,
                            confidence, risk_code, ai_execution_ref,
                            provenance_ref, supersedes_proposal_id, created_at
                        ) VALUES (
                            :id, :proposal_kind, :payload_schema_ref,
                            :payload_schema_version, CAST(:payload AS jsonb),
                            :payload_hash, :run_id, :stage_execution_id,
                            :taxonomy_version, :configuration_version,
                            :methodology_version, :confidence, :risk_code,
                            :ai_execution_ref, :provenance_ref,
                            :supersedes_proposal_id, :created_at
                        )
                        """
                    ),
                    {
                        "id": proposal.id,
                        "proposal_kind": proposal.proposal_kind,
                        "payload_schema_ref": proposal.payload_schema_ref,
                        "payload_schema_version": proposal.payload_schema_version,
                        "payload": json.dumps(proposal.payload),
                        "payload_hash": proposal.payload_hash,
                        "run_id": proposal.run_id,
                        "stage_execution_id": proposal.stage_execution_id,
                        "taxonomy_version": proposal.taxonomy_version,
                        "configuration_version": proposal.configuration_version,
                        "methodology_version": proposal.methodology_version,
                        "confidence": proposal.confidence,
                        "risk_code": proposal.risk_code,
                        "ai_execution_ref": proposal.ai_execution_ref,
                        "provenance_ref": proposal.provenance_ref,
                        "supersedes_proposal_id": proposal.supersedes_proposal_id,
                        "created_at": proposal.created_at,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("proposal conflicts with orchestration state") from exc

    def get_proposal(self, proposal_id: UUID) -> Proposal | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM ingestion.proposal WHERE id = :proposal_id"),
                {"proposal_id": proposal_id},
            ).mappings().one_or_none()
        return self._proposal(row) if row is not None else None

    def list_proposals(self, run_id: UUID) -> tuple[Proposal, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT * FROM ingestion.proposal
                    WHERE run_id = :run_id
                    ORDER BY created_at, id
                    """
                ),
                {"run_id": run_id},
            ).mappings().all()
        return tuple(self._proposal(row) for row in rows)

    def add_review_decision(self, decision: ProposalReviewDecision) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO ingestion.proposal_review_decision (
                            id, proposal_id, decision, reviewer_ref, decided_at,
                            rationale, reason_code, policy_version,
                            risk_policy_version
                        ) VALUES (
                            :id, :proposal_id, :decision, :reviewer_ref,
                            :decided_at, :rationale, :reason_code,
                            :policy_version, :risk_policy_version
                        )
                        """
                    ),
                    {
                        "id": decision.id,
                        "proposal_id": decision.proposal_id,
                        "decision": decision.decision.value,
                        "reviewer_ref": decision.reviewer_ref,
                        "decided_at": decision.decided_at,
                        "rationale": decision.rationale,
                        "reason_code": decision.reason_code,
                        "policy_version": decision.policy_version,
                        "risk_policy_version": decision.risk_policy_version,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("proposal already has a terminal review decision") from exc

    def get_review_decision(
        self,
        proposal_id: UUID,
    ) -> ProposalReviewDecision | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM ingestion.proposal_review_decision
                    WHERE proposal_id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_id},
            ).mappings().one_or_none()
        return self._review(row) if row is not None else None

    @staticmethod
    def _run_params(run: IngestionRun) -> dict[str, object]:
        return {
            "id": run.id,
            "run_key": run.run_key,
            "input_artifact_kind": run.input_artifact_kind.value,
            "input_artifact_id": run.input_artifact_id,
            "input_content_hash": run.input_content_hash,
            "pipeline_code": run.pipeline_code,
            "pipeline_version": run.pipeline_version,
            "configuration_hash": run.configuration_hash,
            "taxonomy_version": run.taxonomy_version,
            "methodology_version": run.methodology_version,
            "locale": run.locale,
            "jurisdiction_code": run.jurisdiction_code,
            "state": run.state.value,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }

    @staticmethod
    def _run(row) -> IngestionRun:
        return IngestionRun(
            id=row["id"],
            run_key=row["run_key"],
            input_artifact_kind=InputArtifactKind(row["input_artifact_kind"]),
            input_artifact_id=row["input_artifact_id"],
            input_content_hash=row["input_content_hash"],
            pipeline_code=row["pipeline_code"],
            pipeline_version=row["pipeline_version"],
            configuration_hash=row["configuration_hash"],
            taxonomy_version=row["taxonomy_version"],
            methodology_version=row["methodology_version"],
            locale=row["locale"],
            jurisdiction_code=row["jurisdiction_code"],
            state=IngestionRunState(row["state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _stage(row) -> StageExecution:
        return StageExecution(
            id=row["id"],
            run_id=row["run_id"],
            stage_code=row["stage_code"],
            stage_version=row["stage_version"],
            attempt_no=row["attempt_no"],
            max_attempts=row["max_attempts"],
            executor_kind=ExecutorKind(row["executor_kind"]),
            input_hash=row["input_hash"],
            output_hash=row["output_hash"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            outcome=StageOutcome(row["outcome"]),
            error_code=row["error_code"],
            execution_ref=row["execution_ref"],
            trace_id=row["trace_id"],
        )

    @staticmethod
    def _proposal(row) -> Proposal:
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return Proposal(
            id=row["id"],
            proposal_kind=row["proposal_kind"],
            payload_schema_ref=row["payload_schema_ref"],
            payload_schema_version=row["payload_schema_version"],
            payload=dict(payload),
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
        )

    @staticmethod
    def _review(row) -> ProposalReviewDecision:
        return ProposalReviewDecision(
            id=row["id"],
            proposal_id=row["proposal_id"],
            decision=ProposalReviewDecisionKind(row["decision"]),
            reviewer_ref=row["reviewer_ref"],
            decided_at=row["decided_at"],
            rationale=row["rationale"],
            reason_code=row["reason_code"],
            policy_version=row["policy_version"],
            risk_policy_version=row["risk_policy_version"],
        )

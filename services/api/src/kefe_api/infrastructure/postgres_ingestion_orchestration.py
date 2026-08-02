from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.ingestion_orchestration.batch import (
    order_successful_stage_batch,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalMaterialization,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
)


class PostgresIngestionOrchestrationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get_run(self, run: IngestionRun) -> IngestionRun:
        source_id = (
            run.input_artifact_id
            if run.input_artifact_kind is InputArtifactKind.SOURCE_ARTIFACT
            else None
        )
        normalized_id = (
            run.input_artifact_id
            if run.input_artifact_kind is InputArtifactKind.NORMALIZED_ARTIFACT
            else None
        )
        with self._engine.begin() as connection:
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO ingestion.ingestion_run (
                        id, run_key, source_artifact_id, normalized_artifact_id,
                        input_content_hash, pipeline_code, pipeline_version,
                        configuration_hash, taxonomy_version, methodology_version,
                        locale, jurisdiction_code, state, created_at, updated_at
                    ) VALUES (
                        :id, :run_key, :source_artifact_id, :normalized_artifact_id,
                        :input_content_hash, :pipeline_code, :pipeline_version,
                        :configuration_hash, :taxonomy_version, :methodology_version,
                        :locale, :jurisdiction_code, :state, :created_at, :updated_at
                    )
                    ON CONFLICT (run_key) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "id": run.id,
                    "run_key": run.run_key,
                    "source_artifact_id": source_id,
                    "normalized_artifact_id": normalized_id,
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
                },
            ).scalar_one_or_none()
            if inserted is not None:
                return run
            row = connection.execute(
                text("SELECT * FROM ingestion.ingestion_run WHERE run_key = :run_key"),
                {"run_key": run.run_key},
            ).mappings().one()
            return self._run_from_row(row)

    def get_run(self, run_id: UUID) -> IngestionRun | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM ingestion.ingestion_run WHERE id = :id"),
                {"id": run_id},
            ).mappings().one_or_none()
        return self._run_from_row(row) if row else None

    def update_run(self, run: IngestionRun) -> None:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE ingestion.ingestion_run
                    SET state = :state, updated_at = :updated_at
                    WHERE id = :id AND run_key = :run_key
                    """
                ),
                {
                    "id": run.id,
                    "run_key": run.run_key,
                    "state": run.state.value,
                    "updated_at": run.updated_at,
                },
            )
            if result.rowcount != 1:
                raise KeyError(run.id)

    def add_stage_execution(self, execution: StageExecution) -> None:
        try:
            with self._engine.begin() as connection:
                self._insert_stage_execution(connection, execution)
        except IntegrityError as exc:
            raise ValueError("ingestion persistence invariant violated") from exc

    def complete_successful_stage(
        self,
        execution: StageExecution,
        proposals: tuple[Proposal, ...],
    ) -> None:
        ordered = order_successful_stage_batch(execution, proposals)
        batch_ids = {proposal.id for proposal in ordered}
        try:
            with self._engine.begin() as connection:
                run_state = connection.execute(
                    text(
                        """
                        SELECT state FROM ingestion.ingestion_run
                        WHERE id = :run_id
                        FOR UPDATE
                        """
                    ),
                    {"run_id": execution.run_id},
                ).scalar_one_or_none()
                if run_state is None:
                    raise KeyError(execution.run_id)
                if run_state != IngestionRunState.RUNNING.value:
                    raise ValueError(
                        "successful stage requires a RUNNING ingestion run"
                    )

                for proposal in ordered:
                    existing = connection.execute(
                        text("SELECT 1 FROM ingestion.proposal WHERE id = :id"),
                        {"id": proposal.id},
                    ).scalar_one_or_none()
                    if existing is not None:
                        raise ValueError("proposal already exists")
                    target_id = proposal.supersedes_proposal_id
                    if target_id is None or target_id in batch_ids:
                        continue
                    target_run_id = connection.execute(
                        text(
                            """
                            SELECT run_id FROM ingestion.proposal
                            WHERE id = :proposal_id
                            """
                        ),
                        {"proposal_id": target_id},
                    ).scalar_one_or_none()
                    if target_run_id is None:
                        raise KeyError(target_id)
                    if target_run_id != execution.run_id:
                        raise ValueError(
                            "proposal cannot supersede a proposal from another run"
                        )

                self._insert_stage_execution(connection, execution)
                for proposal in ordered:
                    self._insert_proposal(connection, proposal)
        except IntegrityError as exc:
            raise ValueError("ingestion persistence invariant violated") from exc

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
        statement = (
            "SELECT * FROM ingestion.stage_execution WHERE "
            + " AND ".join(clauses)
            + " ORDER BY started_at, attempt_no, id"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(text(statement), params).mappings().all()
        return tuple(self._stage_from_row(row) for row in rows)

    def add_proposal(self, proposal: Proposal) -> None:
        try:
            with self._engine.begin() as connection:
                target_id = proposal.supersedes_proposal_id
                if target_id is not None:
                    target_run_id = connection.execute(
                        text(
                            """
                            SELECT run_id FROM ingestion.proposal
                            WHERE id = :proposal_id
                            """
                        ),
                        {"proposal_id": target_id},
                    ).scalar_one_or_none()
                    if target_run_id is None:
                        raise KeyError(target_id)
                    if target_run_id != proposal.run_id:
                        raise ValueError(
                            "proposal cannot supersede a proposal from another run"
                        )
                self._insert_proposal(connection, proposal)
        except IntegrityError as exc:
            raise ValueError("ingestion persistence invariant violated") from exc

    def get_proposal(self, proposal_id: UUID) -> Proposal | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM ingestion.proposal WHERE id = :id"),
                {"id": proposal_id},
            ).mappings().one_or_none()
        return self._proposal_from_row(row) if row else None

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
        return tuple(self._proposal_from_row(row) for row in rows)

    def add_review_decision(self, decision: ProposalReviewDecision) -> None:
        self._insert(
            """
            INSERT INTO ingestion.proposal_review_decision (
                id, proposal_id, decision, reviewer_ref, decided_at,
                rationale, reason_code, policy_version, risk_policy_version
            ) VALUES (
                :id, :proposal_id, :decision, :reviewer_ref, :decided_at,
                :rationale, :reason_code, :policy_version, :risk_policy_version
            )
            """,
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

    def get_review_decision(self, proposal_id: UUID) -> ProposalReviewDecision | None:
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
        return self._review_from_row(row) if row else None

    def add_materialization(self, materialization: ProposalMaterialization) -> None:
        try:
            with self._engine.begin() as connection:
                inserted = connection.execute(
                    text(
                        """
                        INSERT INTO ingestion.proposal_materialization (
                            id, proposal_id, review_decision_id,
                            target_kind, target_id, materialized_at
                        ) VALUES (
                            :id, :proposal_id, :review_decision_id,
                            :target_kind, :target_id, :materialized_at
                        )
                        ON CONFLICT (proposal_id, target_kind) DO NOTHING
                        RETURNING id
                        """
                    ),
                    {
                        "id": materialization.id,
                        "proposal_id": materialization.proposal_id,
                        "review_decision_id": materialization.review_decision_id,
                        "target_kind": materialization.target_kind,
                        "target_id": materialization.target_id,
                        "materialized_at": materialization.materialized_at,
                    },
                ).scalar_one_or_none()
                if inserted is not None:
                    return
                row = connection.execute(
                    text(
                        """
                        SELECT * FROM ingestion.proposal_materialization
                        WHERE proposal_id = :proposal_id AND target_kind = :target_kind
                        """
                    ),
                    {
                        "proposal_id": materialization.proposal_id,
                        "target_kind": materialization.target_kind,
                    },
                ).mappings().one()
                if row["target_id"] != materialization.target_id:
                    raise ValueError(
                        "proposal already materialized to a different target"
                    )
        except IntegrityError as exc:
            raise ValueError("ingestion persistence invariant violated") from exc

    def find_materialization(
        self,
        proposal_id: UUID,
        *,
        target_kind: str | None = None,
    ) -> ProposalMaterialization | None:
        with self._engine.connect() as connection:
            if target_kind is not None:
                row = connection.execute(
                    text(
                        """
                        SELECT * FROM ingestion.proposal_materialization
                        WHERE proposal_id = :proposal_id AND target_kind = :target_kind
                        """
                    ),
                    {"proposal_id": proposal_id, "target_kind": target_kind},
                ).mappings().one_or_none()
                return self._materialization_from_row(row) if row else None
            rows = connection.execute(
                text(
                    """
                    SELECT * FROM ingestion.proposal_materialization
                    WHERE proposal_id = :proposal_id
                    ORDER BY materialized_at, id
                    """
                ),
                {"proposal_id": proposal_id},
            ).mappings().all()
        if not rows:
            return None
        if len(rows) > 1:
            raise ValueError("proposal has multiple materialization target kinds")
        return self._materialization_from_row(rows[0])

    @staticmethod
    def _insert_stage_execution(connection, execution: StageExecution) -> None:
        connection.execute(
            text(
                """
                INSERT INTO ingestion.stage_execution (
                    id, run_id, stage_code, stage_version, attempt_no, max_attempts,
                    executor_kind, input_hash, output_hash, started_at, completed_at,
                    outcome, error_code, execution_ref, trace_id
                ) VALUES (
                    :id, :run_id, :stage_code, :stage_version,
                    :attempt_no, :max_attempts, :executor_kind,
                    :input_hash, :output_hash, :started_at, :completed_at,
                    :outcome, :error_code, :execution_ref, :trace_id
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

    @staticmethod
    def _insert_proposal(connection, proposal: Proposal) -> None:
        connection.execute(
            text(
                """
                INSERT INTO ingestion.proposal (
                    id, proposal_kind, payload_schema_ref, payload_schema_version,
                    payload, payload_hash, run_id, stage_execution_id,
                    taxonomy_version, configuration_version, methodology_version,
                    confidence, risk_code, ai_execution_ref, provenance_ref,
                    supersedes_proposal_id, created_at
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
                "payload": json.dumps(
                    proposal.payload,
                    sort_keys=True,
                    default=str,
                ),
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

    def _insert(self, statement: str, params: dict[str, object]) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(text(statement), params)
        except IntegrityError as exc:
            raise ValueError("ingestion persistence invariant violated") from exc

    @staticmethod
    def _run_from_row(row) -> IngestionRun:
        source_id = row["source_artifact_id"]
        normalized_id = row["normalized_artifact_id"]
        return IngestionRun(
            id=row["id"],
            run_key=row["run_key"],
            input_artifact_kind=(
                InputArtifactKind.SOURCE_ARTIFACT
                if source_id is not None
                else InputArtifactKind.NORMALIZED_ARTIFACT
            ),
            input_artifact_id=source_id if source_id is not None else normalized_id,
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
    def _stage_from_row(row) -> StageExecution:
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
    def _proposal_from_row(row) -> Proposal:
        return Proposal(
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
        )

    @staticmethod
    def _review_from_row(row) -> ProposalReviewDecision:
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

    @staticmethod
    def _materialization_from_row(row) -> ProposalMaterialization:
        return ProposalMaterialization(
            id=row["id"],
            proposal_id=row["proposal_id"],
            review_decision_id=row["review_decision_id"],
            target_kind=row["target_kind"],
            target_id=row["target_id"],
            materialized_at=row["materialized_at"],
        )

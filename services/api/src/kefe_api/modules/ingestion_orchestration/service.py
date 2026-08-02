from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

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
    build_run_key,
    stable_payload_hash,
    utcnow,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
    ProposalTargetMaterializer,
    StageProcessor,
)


@dataclass(frozen=True, slots=True)
class RetryableStageError(Exception):
    code: str


@dataclass(frozen=True, slots=True)
class FinalStageError(Exception):
    code: str


class IngestionOrchestrationService:
    def __init__(self, repository: IngestionOrchestrationRepository) -> None:
        self._repository = repository

    def start_run(
        self,
        *,
        input_artifact_kind: InputArtifactKind,
        input_artifact_id: UUID,
        input_content_hash: str,
        pipeline_code: str,
        pipeline_version: str,
        configuration_hash: str,
        taxonomy_version: str | None = None,
        methodology_version: str | None = None,
        locale: str | None = None,
        jurisdiction_code: str | None = None,
    ) -> IngestionRun:
        now = utcnow()
        run = IngestionRun(
            id=uuid4(),
            run_key=build_run_key(
                input_artifact_kind=input_artifact_kind,
                input_artifact_id=input_artifact_id,
                input_content_hash=input_content_hash,
                pipeline_code=pipeline_code,
                pipeline_version=pipeline_version,
                configuration_hash=configuration_hash,
                taxonomy_version=taxonomy_version,
                methodology_version=methodology_version,
                locale=locale,
                jurisdiction_code=jurisdiction_code,
            ),
            input_artifact_kind=input_artifact_kind,
            input_artifact_id=input_artifact_id,
            input_content_hash=input_content_hash,
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
            configuration_hash=configuration_hash,
            taxonomy_version=taxonomy_version,
            methodology_version=methodology_version,
            locale=locale,
            jurisdiction_code=jurisdiction_code,
            state=IngestionRunState.QUEUED,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create_or_get_run(run)

    def execute_stage(
        self,
        *,
        run_id: UUID,
        stage_code: str,
        stage_version: str,
        input_hash: str,
        max_attempts: int,
        executor_kind: ExecutorKind,
        processor: StageProcessor,
        execution_ref: str | None = None,
        trace_id: str | None = None,
        before_persist: Callable[[], None] | None = None,
    ) -> StageExecution:
        run = self._require_run(run_id)
        if run.state is IngestionRunState.QUEUED:
            run = run.transition(IngestionRunState.RUNNING)
            self._repository.update_run(run)
        elif run.state is not IngestionRunState.RUNNING:
            raise ValueError(f"run is not executable from state {run.state}")

        prior = self._repository.list_stage_executions(
            run_id,
            stage_code=stage_code,
            stage_version=stage_version,
        )
        attempt_no = len(prior) + 1
        if max_attempts < 1 or attempt_no > max_attempts:
            raise ValueError("stage retry limit exhausted")

        started_at = utcnow()
        try:
            result = processor.process(
                run=run,
                stage_code=stage_code,
                stage_version=stage_version,
                input_hash=input_hash,
            )
        except RetryableStageError as exc:
            self._admit_persistence(before_persist)
            outcome = (
                StageOutcome.FAILED_RETRYABLE
                if attempt_no < max_attempts
                else StageOutcome.FAILED_FINAL
            )
            execution = StageExecution(
                id=uuid4(),
                run_id=run_id,
                stage_code=stage_code,
                stage_version=stage_version,
                attempt_no=attempt_no,
                max_attempts=max_attempts,
                executor_kind=executor_kind,
                input_hash=input_hash,
                started_at=started_at,
                outcome=outcome,
                error_code=exc.code,
                completed_at=utcnow(),
                execution_ref=execution_ref,
                trace_id=trace_id,
            )
            self._repository.add_stage_execution(execution)
            self._repository.update_run(
                run.transition(
                    IngestionRunState.FAILED_RETRYABLE
                    if outcome is StageOutcome.FAILED_RETRYABLE
                    else IngestionRunState.FAILED_FINAL
                )
            )
            return execution
        except FinalStageError as exc:
            self._admit_persistence(before_persist)
            execution = StageExecution(
                id=uuid4(),
                run_id=run_id,
                stage_code=stage_code,
                stage_version=stage_version,
                attempt_no=attempt_no,
                max_attempts=max_attempts,
                executor_kind=executor_kind,
                input_hash=input_hash,
                started_at=started_at,
                outcome=StageOutcome.FAILED_FINAL,
                error_code=exc.code,
                completed_at=utcnow(),
                execution_ref=execution_ref,
                trace_id=trace_id,
            )
            self._repository.add_stage_execution(execution)
            self._repository.update_run(run.transition(IngestionRunState.FAILED_FINAL))
            return execution
        except Exception:
            self._admit_persistence(before_persist)
            execution = StageExecution(
                id=uuid4(),
                run_id=run_id,
                stage_code=stage_code,
                stage_version=stage_version,
                attempt_no=attempt_no,
                max_attempts=max_attempts,
                executor_kind=executor_kind,
                input_hash=input_hash,
                started_at=started_at,
                outcome=StageOutcome.FAILED_FINAL,
                error_code="UNEXPECTED_STAGE_FAILURE",
                completed_at=utcnow(),
                execution_ref=execution_ref,
                trace_id=trace_id,
            )
            self._repository.add_stage_execution(execution)
            self._repository.update_run(run.transition(IngestionRunState.FAILED_FINAL))
            return execution

        self._admit_persistence(before_persist)
        completed_at = utcnow()
        execution = StageExecution(
            id=uuid4(),
            run_id=run_id,
            stage_code=stage_code,
            stage_version=stage_version,
            attempt_no=attempt_no,
            max_attempts=max_attempts,
            executor_kind=executor_kind,
            input_hash=input_hash,
            started_at=started_at,
            outcome=StageOutcome.SUCCEEDED,
            output_hash=result.output_hash,
            completed_at=completed_at,
            execution_ref=execution_ref,
            trace_id=trace_id,
        )
        proposals = tuple(
            Proposal(
                id=uuid4(),
                proposal_kind=draft.proposal_kind,
                payload_schema_ref=draft.payload_schema_ref,
                payload_schema_version=draft.payload_schema_version,
                payload=draft.payload,
                payload_hash=stable_payload_hash(draft.payload),
                run_id=run_id,
                stage_execution_id=execution.id,
                created_at=completed_at,
                taxonomy_version=draft.taxonomy_version,
                configuration_version=draft.configuration_version,
                methodology_version=draft.methodology_version,
                confidence=draft.confidence,
                risk_code=draft.risk_code,
                ai_execution_ref=draft.ai_execution_ref,
                provenance_ref=draft.provenance_ref,
                supersedes_proposal_id=draft.supersedes_proposal_id,
            )
            for draft in result.proposals
        )
        self._repository.complete_successful_stage(execution, proposals)
        return execution

    def requeue(self, run_id: UUID) -> IngestionRun:
        run = self._require_run(run_id)
        queued = run.transition(IngestionRunState.QUEUED)
        self._repository.update_run(queued)
        return queued

    def mark_succeeded(self, run_id: UUID) -> IngestionRun:
        run = self._require_run(run_id)
        completed = run.transition(IngestionRunState.SUCCEEDED)
        self._repository.update_run(completed)
        return completed

    def cancel(self, run_id: UUID) -> IngestionRun:
        run = self._require_run(run_id)
        canceled = run.transition(IngestionRunState.CANCELED)
        self._repository.update_run(canceled)
        return canceled

    def review_proposal(
        self,
        *,
        proposal_id: UUID,
        decision: ProposalReviewDecisionKind,
        reviewer_ref: str,
        rationale: str | None = None,
        reason_code: str | None = None,
        policy_version: str | None = None,
        risk_policy_version: str | None = None,
    ) -> ProposalReviewDecision:
        if self._repository.get_proposal(proposal_id) is None:
            raise KeyError(proposal_id)
        review = ProposalReviewDecision(
            id=uuid4(),
            proposal_id=proposal_id,
            decision=decision,
            reviewer_ref=reviewer_ref,
            decided_at=utcnow(),
            rationale=rationale,
            reason_code=reason_code,
            policy_version=policy_version,
            risk_policy_version=risk_policy_version,
        )
        self._repository.add_review_decision(review)
        return review

    def materialize_accepted_proposal(
        self,
        *,
        proposal_id: UUID,
        materializer: ProposalTargetMaterializer,
    ) -> ProposalMaterialization:
        proposal = self._repository.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        review = self._repository.get_review_decision(proposal_id)
        if review is None or review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise ValueError("proposal must have an ACCEPTED review decision")

        existing = self._repository.find_materialization(proposal_id)
        if existing is not None:
            return existing

        target_kind, target_id = materializer.materialize(
            proposal=proposal,
            review=review,
        )
        materialization = ProposalMaterialization(
            id=uuid4(),
            proposal_id=proposal_id,
            review_decision_id=review.id,
            target_kind=target_kind,
            target_id=target_id,
            materialized_at=utcnow(),
        )
        self._repository.add_materialization(materialization)
        return self._repository.find_materialization(
            proposal_id,
            target_kind=target_kind,
        ) or materialization

    @staticmethod
    def _admit_persistence(before_persist: Callable[[], None] | None) -> None:
        if before_persist is not None:
            before_persist()

    def _require_run(self, run_id: UUID) -> IngestionRun:
        run = self._repository.get_run(run_id)
        if run is None:
            raise KeyError(run_id)
        return run

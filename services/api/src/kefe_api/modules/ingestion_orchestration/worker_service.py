from __future__ import annotations

from collections.abc import Callable
from time import monotonic_ns
from uuid import UUID, uuid4

from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseError,
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLeaseClaim,
    IngestionRunLeaseReleaseDisposition,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRunState,
    StageExecution,
    StageOutcome,
    utcnow,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionRuntimePlan,
    IngestionRuntimeStage,
    IngestionWorkerObserver,
    IngestionWorkerRunOutcome,
    IngestionWorkerRunResult,
    IngestionWorkerRuntimeRegistry,
)


class IngestionWorkerRunner:
    def __init__(
        self,
        *,
        repository: IngestionOrchestrationRepository,
        orchestration: IngestionOrchestrationService,
        leases: IngestionRunLeaseService,
        registry: IngestionWorkerRuntimeRegistry,
        observer: IngestionWorkerObserver,
        clock=utcnow,
        monotonic_clock: Callable[[], int] = monotonic_ns,
    ) -> None:
        self._repository = repository
        self._orchestration = orchestration
        self._leases = leases
        self._registry = registry
        self._observer = observer
        self._clock = clock
        self._monotonic_clock = monotonic_clock

    def run_once(
        self,
        *,
        worker_ref: str,
        pipeline_code: str,
        pipeline_version: str,
        ttl_seconds: int,
        trace_id: str | None = None,
    ) -> IngestionWorkerRunResult:
        started_ns = self._monotonic_clock()
        resolved_trace_id = trace_id or str(uuid4())
        try:
            plan = self._registry.get_plan(
                pipeline_code=pipeline_code,
                pipeline_version=pipeline_version,
            )
        except KeyError:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=IngestionWorkerRunOutcome.BLOCKED,
                    worker_ref=worker_ref,
                    pipeline_code=pipeline_code,
                    pipeline_version=pipeline_version,
                    trace_id=resolved_trace_id,
                    error_code="INGESTION_PIPELINE_NOT_REGISTERED",
                )
            )

        claim = self._leases.claim_next(
            worker_ref=worker_ref,
            ttl_seconds=ttl_seconds,
            pipeline_code=plan.pipeline_code,
            pipeline_version=plan.pipeline_version,
            now=self._clock(),
        )
        if claim is None:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=IngestionWorkerRunOutcome.IDLE,
                    worker_ref=worker_ref,
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    trace_id=resolved_trace_id,
                )
            )

        try:
            return self._run_claimed(
                claim=claim,
                plan=plan,
                worker_ref=worker_ref,
                ttl_seconds=ttl_seconds,
                trace_id=resolved_trace_id,
                started_ns=started_ns,
            )
        except IngestionRunLeaseError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=IngestionWorkerRunOutcome.LEASE_LOST,
                    worker_ref=worker_ref,
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    trace_id=resolved_trace_id,
                    run_id=claim.run.id,
                    lease_id=claim.lease.id,
                    error_code=exc.code,
                )
            )
        except Exception:
            return self._handle_unexpected(
                claim=claim,
                plan=plan,
                worker_ref=worker_ref,
                trace_id=resolved_trace_id,
                started_ns=started_ns,
            )

    def _run_claimed(
        self,
        *,
        claim: IngestionRunLeaseClaim,
        plan: IngestionRuntimePlan,
        worker_ref: str,
        ttl_seconds: int,
        trace_id: str,
        started_ns: int,
    ) -> IngestionWorkerRunResult:
        run = claim.run
        lease = claim.lease
        if run.pipeline_code != plan.pipeline_code or run.pipeline_version != plan.pipeline_version:
            return self._block_and_requeue(
                claim=claim,
                plan=plan,
                worker_ref=worker_ref,
                trace_id=trace_id,
                started_ns=started_ns,
                error_code="INGESTION_CLAIM_PLAN_MISMATCH",
            )

        all_history = self._repository.list_stage_executions(run.id)
        known = plan.stage_identities
        unknown = next(
            (
                execution
                for execution in all_history
                if (execution.stage_code, execution.stage_version) not in known
            ),
            None,
        )
        if unknown is not None:
            return self._block_and_requeue(
                claim=claim,
                plan=plan,
                worker_ref=worker_ref,
                trace_id=trace_id,
                started_ns=started_ns,
                stage_code=unknown.stage_code,
                stage_version=unknown.stage_version,
                stage_attempt=unknown.attempt_no,
                error_code="INGESTION_PIPELINE_HISTORY_INVALID",
            )

        input_hash = run.input_content_hash
        completed_stage_count = 0
        for stage in plan.stages:
            prior = self._repository.list_stage_executions(
                run.id,
                stage_code=stage.stage_code,
                stage_version=stage.stage_version,
            )
            invalid = self._validate_stage_history(
                prior=prior,
                stage=stage,
                expected_input_hash=input_hash,
            )
            if invalid is not None:
                return self._block_and_requeue(
                    claim=claim,
                    plan=plan,
                    worker_ref=worker_ref,
                    trace_id=trace_id,
                    started_ns=started_ns,
                    stage_code=stage.stage_code,
                    stage_version=stage.stage_version,
                    stage_attempt=prior[-1].attempt_no if prior else None,
                    completed_stage_count=completed_stage_count,
                    error_code=invalid,
                )

            successful = self._successful_execution(prior)
            if successful is not None:
                assert successful.output_hash is not None
                input_hash = successful.output_hash
                completed_stage_count += 1
                continue

            self._heartbeat(
                lease_id=lease.id,
                worker_ref=worker_ref,
                ttl_seconds=ttl_seconds,
            )
            try:
                processor = self._registry.get_processor(
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    stage_code=stage.stage_code,
                    stage_version=stage.stage_version,
                )
            except KeyError:
                return self._block_and_requeue(
                    claim=claim,
                    plan=plan,
                    worker_ref=worker_ref,
                    trace_id=trace_id,
                    started_ns=started_ns,
                    stage_code=stage.stage_code,
                    stage_version=stage.stage_version,
                    completed_stage_count=completed_stage_count,
                    error_code="INGESTION_STAGE_PROCESSOR_NOT_REGISTERED",
                )

            execution = self._orchestration.execute_stage(
                run_id=run.id,
                stage_code=stage.stage_code,
                stage_version=stage.stage_version,
                input_hash=input_hash,
                max_attempts=stage.max_attempts,
                executor_kind=stage.executor_kind,
                processor=processor,
                execution_ref=f"lease:{lease.id}",
                trace_id=trace_id,
                before_persist=lambda: self._heartbeat(
                    lease_id=lease.id,
                    worker_ref=worker_ref,
                    ttl_seconds=ttl_seconds,
                ),
            )
            if execution.outcome is StageOutcome.SUCCEEDED:
                assert execution.output_hash is not None
                input_hash = execution.output_hash
                completed_stage_count += 1
                continue

            self._leases.release(
                lease_id=lease.id,
                worker_ref=worker_ref,
                disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
                now=self._clock(),
            )
            outcome = (
                IngestionWorkerRunOutcome.RETRYABLE_FAILURE
                if execution.outcome is StageOutcome.FAILED_RETRYABLE
                else IngestionWorkerRunOutcome.FINAL_FAILURE
            )
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=outcome,
                    worker_ref=worker_ref,
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    trace_id=trace_id,
                    run_id=run.id,
                    lease_id=lease.id,
                    stage_code=stage.stage_code,
                    stage_version=stage.stage_version,
                    completed_stage_count=completed_stage_count,
                    stage_attempt=execution.attempt_no,
                    error_code=execution.error_code,
                )
            )

        self._heartbeat(
            lease_id=lease.id,
            worker_ref=worker_ref,
            ttl_seconds=ttl_seconds,
        )
        self._orchestration.mark_succeeded(run.id)
        self._leases.release(
            lease_id=lease.id,
            worker_ref=worker_ref,
            disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
            now=self._clock(),
        )
        return self._emit(
            self._result(
                started_ns=started_ns,
                outcome=IngestionWorkerRunOutcome.SUCCEEDED,
                worker_ref=worker_ref,
                pipeline_code=plan.pipeline_code,
                pipeline_version=plan.pipeline_version,
                trace_id=trace_id,
                run_id=run.id,
                lease_id=lease.id,
                completed_stage_count=completed_stage_count,
            )
        )

    @staticmethod
    def _successful_execution(
        prior: tuple[StageExecution, ...],
    ) -> StageExecution | None:
        successes = tuple(
            execution
            for execution in prior
            if execution.outcome is StageOutcome.SUCCEEDED
        )
        return successes[0] if len(successes) == 1 else None

    @staticmethod
    def _validate_stage_history(
        *,
        prior: tuple[StageExecution, ...],
        stage: IngestionRuntimeStage,
        expected_input_hash: str,
    ) -> str | None:
        if not prior:
            return None
        if any(
            execution.max_attempts != stage.max_attempts
            or execution.executor_kind is not stage.executor_kind
            or execution.input_hash != expected_input_hash
            for execution in prior
        ):
            return "INGESTION_STAGE_HISTORY_PLAN_DRIFT"
        successes = tuple(
            execution
            for execution in prior
            if execution.outcome is StageOutcome.SUCCEEDED
        )
        if len(successes) > 1:
            return "INGESTION_STAGE_HISTORY_MULTIPLE_SUCCESS"
        if successes and prior[-1].outcome is not StageOutcome.SUCCEEDED:
            return "INGESTION_STAGE_HISTORY_AFTER_SUCCESS"
        if not successes and prior[-1].outcome is not StageOutcome.FAILED_RETRYABLE:
            return "INGESTION_STAGE_HISTORY_NOT_RESUMABLE"
        if len(prior) >= stage.max_attempts and not successes:
            return "INGESTION_STAGE_RETRY_LIMIT_EXHAUSTED"
        return None

    def _heartbeat(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        ttl_seconds: int,
    ) -> None:
        self._leases.heartbeat(
            lease_id=lease_id,
            worker_ref=worker_ref,
            ttl_seconds=ttl_seconds,
            now=self._clock(),
        )

    def _block_and_requeue(
        self,
        *,
        claim: IngestionRunLeaseClaim,
        plan: IngestionRuntimePlan,
        worker_ref: str,
        trace_id: str,
        started_ns: int,
        error_code: str,
        stage_code: str | None = None,
        stage_version: str | None = None,
        stage_attempt: int | None = None,
        completed_stage_count: int = 0,
    ) -> IngestionWorkerRunResult:
        try:
            self._leases.release(
                lease_id=claim.lease.id,
                worker_ref=worker_ref,
                disposition=IngestionRunLeaseReleaseDisposition.REQUEUE,
                now=self._clock(),
            )
        except IngestionRunLeaseError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=IngestionWorkerRunOutcome.LEASE_LOST,
                    worker_ref=worker_ref,
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    trace_id=trace_id,
                    run_id=claim.run.id,
                    lease_id=claim.lease.id,
                    stage_code=stage_code,
                    stage_version=stage_version,
                    completed_stage_count=completed_stage_count,
                    stage_attempt=stage_attempt,
                    error_code=exc.code,
                )
            )
        return self._emit(
            self._result(
                started_ns=started_ns,
                outcome=IngestionWorkerRunOutcome.BLOCKED,
                worker_ref=worker_ref,
                pipeline_code=plan.pipeline_code,
                pipeline_version=plan.pipeline_version,
                trace_id=trace_id,
                run_id=claim.run.id,
                lease_id=claim.lease.id,
                stage_code=stage_code,
                stage_version=stage_version,
                completed_stage_count=completed_stage_count,
                stage_attempt=stage_attempt,
                error_code=error_code,
            )
        )

    def _handle_unexpected(
        self,
        *,
        claim: IngestionRunLeaseClaim,
        plan: IngestionRuntimePlan,
        worker_ref: str,
        trace_id: str,
        started_ns: int,
    ) -> IngestionWorkerRunResult:
        run = self._repository.get_run(claim.run.id)
        disposition = (
            IngestionRunLeaseReleaseDisposition.REQUEUE
            if run is not None and run.state is IngestionRunState.RUNNING
            else IngestionRunLeaseReleaseDisposition.TERMINAL
        )
        try:
            self._leases.release(
                lease_id=claim.lease.id,
                worker_ref=worker_ref,
                disposition=disposition,
                now=self._clock(),
            )
        except IngestionRunLeaseError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=IngestionWorkerRunOutcome.LEASE_LOST,
                    worker_ref=worker_ref,
                    pipeline_code=plan.pipeline_code,
                    pipeline_version=plan.pipeline_version,
                    trace_id=trace_id,
                    run_id=claim.run.id,
                    lease_id=claim.lease.id,
                    error_code=exc.code,
                )
            )
        return self._emit(
            self._result(
                started_ns=started_ns,
                outcome=IngestionWorkerRunOutcome.BLOCKED,
                worker_ref=worker_ref,
                pipeline_code=plan.pipeline_code,
                pipeline_version=plan.pipeline_version,
                trace_id=trace_id,
                run_id=claim.run.id,
                lease_id=claim.lease.id,
                error_code="INGESTION_WORKER_UNEXPECTED_FAILURE",
            )
        )

    def _result(
        self,
        *,
        started_ns: int,
        outcome: IngestionWorkerRunOutcome,
        worker_ref: str,
        pipeline_code: str,
        pipeline_version: str,
        trace_id: str,
        run_id: UUID | None = None,
        lease_id: UUID | None = None,
        stage_code: str | None = None,
        stage_version: str | None = None,
        completed_stage_count: int = 0,
        stage_attempt: int | None = None,
        error_code: str | None = None,
    ) -> IngestionWorkerRunResult:
        elapsed_ns = max(0, self._monotonic_clock() - started_ns)
        return IngestionWorkerRunResult(
            outcome=outcome,
            worker_ref=worker_ref,
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
            trace_id=trace_id,
            run_id=run_id,
            lease_id=lease_id,
            stage_code=stage_code,
            stage_version=stage_version,
            completed_stage_count=completed_stage_count,
            stage_attempt=stage_attempt,
            duration_ms=elapsed_ns // 1_000_000,
            error_code=error_code,
        )

    def _emit(self, result: IngestionWorkerRunResult) -> IngestionWorkerRunResult:
        self._observer.record(result)
        return result

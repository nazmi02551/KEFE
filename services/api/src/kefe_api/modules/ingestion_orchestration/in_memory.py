from __future__ import annotations

from copy import deepcopy
from threading import RLock
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.batch import (
    order_successful_stage_batch,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    Proposal,
    ProposalMaterialization,
    ProposalReviewDecision,
    StageExecution,
)
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueCountQuery,
    ProposalQueueQuery,
    ProposalQueueRecord,
)


class InMemoryIngestionOrchestrationRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._runs: dict[UUID, IngestionRun] = {}
        self._run_keys: dict[str, UUID] = {}
        self._stage_executions: dict[UUID, StageExecution] = {}
        self._proposals: dict[UUID, Proposal] = {}
        self._review_decisions: dict[UUID, ProposalReviewDecision] = {}
        self._materializations: dict[tuple[UUID, str], ProposalMaterialization] = {}

    def create_or_get_run(self, run: IngestionRun) -> IngestionRun:
        with self._lock:
            existing_id = self._run_keys.get(run.run_key)
            if existing_id is not None:
                return deepcopy(self._runs[existing_id])
            if run.id in self._runs:
                raise ValueError("ingestion run already exists")
            self._runs[run.id] = deepcopy(run)
            self._run_keys[run.run_key] = run.id
            return deepcopy(run)

    def get_run(self, run_id: UUID) -> IngestionRun | None:
        with self._lock:
            run = self._runs.get(run_id)
            return deepcopy(run) if run else None

    def update_run(self, run: IngestionRun) -> None:
        with self._lock:
            current = self._runs.get(run.id)
            if current is None:
                raise KeyError(run.id)
            if current.run_key != run.run_key:
                raise ValueError("run_key is immutable")
            self._runs[run.id] = deepcopy(run)

    def add_stage_execution(self, execution: StageExecution) -> None:
        with self._lock:
            self._require_run(execution.run_id)
            self._validate_stage_execution_available(execution)
            self._stage_executions[execution.id] = deepcopy(execution)

    def complete_successful_stage(
        self,
        execution: StageExecution,
        proposals: tuple[Proposal, ...],
    ) -> None:
        with self._lock:
            run = self._runs.get(execution.run_id)
            if run is None:
                raise KeyError(execution.run_id)
            if run.state is not IngestionRunState.RUNNING:
                raise ValueError("successful stage requires a RUNNING ingestion run")

            ordered = order_successful_stage_batch(execution, proposals)
            self._validate_stage_execution_available(execution)
            batch_ids = {proposal.id for proposal in ordered}
            for proposal in ordered:
                if proposal.id in self._proposals:
                    raise ValueError("proposal already exists")
                target_id = proposal.supersedes_proposal_id
                if target_id is None or target_id in batch_ids:
                    continue
                target = self._proposals.get(target_id)
                if target is None:
                    raise KeyError(target_id)
                if target.run_id != execution.run_id:
                    raise ValueError("proposal cannot supersede a proposal from another run")

            execution_copy = deepcopy(execution)
            proposal_copies = tuple(deepcopy(proposal) for proposal in ordered)
            self._stage_executions[execution.id] = execution_copy
            for proposal in proposal_copies:
                self._proposals[proposal.id] = proposal

    def list_stage_executions(
        self,
        run_id: UUID,
        *,
        stage_code: str | None = None,
        stage_version: str | None = None,
    ) -> tuple[StageExecution, ...]:
        with self._lock:
            items = [
                item
                for item in self._stage_executions.values()
                if item.run_id == run_id
                and (stage_code is None or item.stage_code == stage_code)
                and (stage_version is None or item.stage_version == stage_version)
            ]
            return tuple(
                deepcopy(item)
                for item in sorted(
                    items,
                    key=lambda value: (value.started_at, value.attempt_no),
                )
            )

    def add_proposal(self, proposal: Proposal) -> None:
        with self._lock:
            self._require_run(proposal.run_id)
            execution = self._stage_executions.get(proposal.stage_execution_id)
            if execution is None:
                raise KeyError(proposal.stage_execution_id)
            if execution.run_id != proposal.run_id:
                raise ValueError("proposal stage execution belongs to another run")
            if proposal.supersedes_proposal_id is not None:
                superseded = self._proposals.get(proposal.supersedes_proposal_id)
                if superseded is None:
                    raise KeyError(proposal.supersedes_proposal_id)
                if superseded.run_id != proposal.run_id:
                    raise ValueError("proposal cannot supersede a proposal from another run")
            if proposal.id in self._proposals:
                raise ValueError("proposal already exists")
            self._proposals[proposal.id] = deepcopy(proposal)

    def get_proposal(self, proposal_id: UUID) -> Proposal | None:
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            return deepcopy(proposal) if proposal else None

    def list_proposals(self, run_id: UUID) -> tuple[Proposal, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        proposal
                        for proposal in self._proposals.values()
                        if proposal.run_id == run_id
                    ),
                    key=lambda value: (value.created_at, str(value.id)),
                )
            )

    def list_proposal_queue(
        self,
        query: ProposalQueueQuery,
    ) -> tuple[ProposalQueueRecord, ...]:
        with self._lock:
            records: list[ProposalQueueRecord] = []
            for proposal in self._proposals.values():
                run = self._runs[proposal.run_id]
                review = self._review_decisions.get(proposal.id)
                record = ProposalQueueRecord(
                    proposal=proposal,
                    run=run,
                    review=review,
                )
                if not self._matches_queue_query(record, query):
                    continue
                records.append(record)
            records.sort(key=lambda item: (item.proposal.created_at, str(item.proposal.id)))
            return tuple(deepcopy(item) for item in records[: query.limit])

    def count_proposal_queue(self, query: ProposalQueueCountQuery) -> int:
        with self._lock:
            return sum(
                1
                for proposal in self._proposals.values()
                if self._matches_count_query(
                    ProposalQueueRecord(
                        proposal=proposal,
                        run=self._runs[proposal.run_id],
                        review=self._review_decisions.get(proposal.id),
                    ),
                    query,
                )
            )

    def get_proposal_queue_record(
        self,
        proposal_id: UUID,
    ) -> ProposalQueueRecord | None:
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                return None
            return deepcopy(
                ProposalQueueRecord(
                    proposal=proposal,
                    run=self._runs[proposal.run_id],
                    review=self._review_decisions.get(proposal_id),
                )
            )

    def add_review_decision(self, decision: ProposalReviewDecision) -> None:
        with self._lock:
            if decision.proposal_id not in self._proposals:
                raise KeyError(decision.proposal_id)
            if decision.proposal_id in self._review_decisions:
                raise ValueError("proposal already has a terminal review decision")
            self._review_decisions[decision.proposal_id] = deepcopy(decision)

    def get_review_decision(self, proposal_id: UUID) -> ProposalReviewDecision | None:
        with self._lock:
            decision = self._review_decisions.get(proposal_id)
            return deepcopy(decision) if decision else None

    def add_materialization(self, materialization: ProposalMaterialization) -> None:
        with self._lock:
            decision = self._review_decisions.get(materialization.proposal_id)
            if decision is None:
                raise KeyError(materialization.proposal_id)
            if decision.id != materialization.review_decision_id:
                raise ValueError("materialization review decision mismatch")
            key = (materialization.proposal_id, materialization.target_kind)
            existing = self._materializations.get(key)
            if existing is not None:
                if existing.target_id == materialization.target_id:
                    return
                raise ValueError("proposal already materialized to a different target")
            self._materializations[key] = deepcopy(materialization)

    def find_materialization(
        self,
        proposal_id: UUID,
        *,
        target_kind: str | None = None,
    ) -> ProposalMaterialization | None:
        with self._lock:
            if target_kind is not None:
                item = self._materializations.get((proposal_id, target_kind))
                return deepcopy(item) if item else None
            matches = [
                item
                for (current_proposal_id, _), item in self._materializations.items()
                if current_proposal_id == proposal_id
            ]
            if not matches:
                return None
            if len(matches) > 1:
                raise ValueError("proposal has multiple materialization target kinds")
            return deepcopy(matches[0])

    @staticmethod
    def _matches_queue_query(
        record: ProposalQueueRecord,
        query: ProposalQueueQuery,
    ) -> bool:
        if not InMemoryIngestionOrchestrationRepository._matches_count_query(
            record,
            ProposalQueueCountQuery(
                review_state=query.review_state,
                proposal_kind=query.proposal_kind,
                risk_code=query.risk_code,
                run_id=query.run_id,
                pipeline_code=query.pipeline_code,
            ),
        ):
            return False
        proposal = record.proposal
        if query.proposal_kind is not None and proposal.proposal_kind != query.proposal_kind:
            return False
        if query.risk_code is not None and proposal.risk_code != query.risk_code:
            return False
        if query.run_id is not None and proposal.run_id != query.run_id:
            return False
        if query.after_created_at is not None:
            assert query.after_proposal_id is not None
            key = (proposal.created_at, str(proposal.id))
            cursor_key = (query.after_created_at, str(query.after_proposal_id))
            if key <= cursor_key:
                return False
        return True

    @staticmethod
    def _matches_count_query(
        record: ProposalQueueRecord,
        query: ProposalQueueCountQuery,
    ) -> bool:
        proposal = record.proposal
        run = record.run
        if query.review_state is not None and record.review_state != query.review_state:
            return False
        if query.proposal_kind is not None and proposal.proposal_kind != query.proposal_kind:
            return False
        if query.risk_code is not None and proposal.risk_code != query.risk_code:
            return False
        if query.run_id is not None and proposal.run_id != query.run_id:
            return False
        if query.pipeline_code is not None and run.pipeline_code != query.pipeline_code:
            return False
        return True

    def _validate_stage_execution_available(self, execution: StageExecution) -> None:
        if execution.id in self._stage_executions:
            raise ValueError("stage execution already exists")
        for current in self._stage_executions.values():
            if (
                current.run_id == execution.run_id
                and current.stage_code == execution.stage_code
                and current.stage_version == execution.stage_version
                and current.attempt_no == execution.attempt_no
            ):
                raise ValueError("stage attempt already exists")

    def _require_run(self, run_id: UUID) -> None:
        if run_id not in self._runs:
            raise KeyError(run_id)

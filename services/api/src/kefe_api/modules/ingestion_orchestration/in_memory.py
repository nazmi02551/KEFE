from __future__ import annotations

from copy import deepcopy
from threading import RLock
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    Proposal,
    ProposalReviewDecision,
    StageExecution,
)


class InMemoryIngestionOrchestrationRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._runs: dict[UUID, IngestionRun] = {}
        self._run_keys: dict[str, UUID] = {}
        self._stage_executions: dict[UUID, StageExecution] = {}
        self._proposals: dict[UUID, Proposal] = {}
        self._review_decisions: dict[UUID, ProposalReviewDecision] = {}

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
            item = self._runs.get(run_id)
            return deepcopy(item) if item is not None else None

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
            if execution.run_id not in self._runs:
                raise KeyError(execution.run_id)
            if execution.id in self._stage_executions:
                raise ValueError("stage execution already exists")
            if any(
                current.run_id == execution.run_id
                and current.stage_code == execution.stage_code
                and current.stage_version == execution.stage_version
                and current.attempt_no == execution.attempt_no
                for current in self._stage_executions.values()
            ):
                raise ValueError("stage attempt already exists")
            self._stage_executions[execution.id] = deepcopy(execution)

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
                    key=lambda value: (value.started_at, value.attempt_no, str(value.id)),
                )
            )

    def add_proposal(self, proposal: Proposal) -> None:
        with self._lock:
            if proposal.run_id not in self._runs:
                raise KeyError(proposal.run_id)
            execution = self._stage_executions.get(proposal.stage_execution_id)
            if execution is None:
                raise KeyError(proposal.stage_execution_id)
            if execution.run_id != proposal.run_id:
                raise ValueError("proposal stage belongs to another run")
            if (
                proposal.supersedes_proposal_id is not None
                and proposal.supersedes_proposal_id not in self._proposals
            ):
                raise KeyError(proposal.supersedes_proposal_id)
            if proposal.id in self._proposals:
                raise ValueError("proposal already exists")
            self._proposals[proposal.id] = deepcopy(proposal)

    def get_proposal(self, proposal_id: UUID) -> Proposal | None:
        with self._lock:
            item = self._proposals.get(proposal_id)
            return deepcopy(item) if item is not None else None

    def list_proposals(self, run_id: UUID) -> tuple[Proposal, ...]:
        with self._lock:
            items = [item for item in self._proposals.values() if item.run_id == run_id]
            return tuple(
                deepcopy(item)
                for item in sorted(items, key=lambda value: (value.created_at, str(value.id)))
            )

    def list_pending_proposals(
        self,
        *,
        proposal_kind: str | None = None,
        limit: int = 50,
    ) -> tuple[Proposal, ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._lock:
            items = [
                item
                for item in self._proposals.values()
                if item.id not in self._review_decisions
                and (proposal_kind is None or item.proposal_kind == proposal_kind)
            ]
            ordered = sorted(items, key=lambda value: (value.created_at, str(value.id)))
            return tuple(deepcopy(item) for item in ordered[:limit])

    def add_review_decision(self, decision: ProposalReviewDecision) -> None:
        with self._lock:
            if decision.proposal_id not in self._proposals:
                raise KeyError(decision.proposal_id)
            if decision.proposal_id in self._review_decisions:
                raise ValueError("proposal already has a terminal review decision")
            self._review_decisions[decision.proposal_id] = deepcopy(decision)

    def get_review_decision(
        self,
        proposal_id: UUID,
    ) -> ProposalReviewDecision | None:
        with self._lock:
            item = self._review_decisions.get(proposal_id)
            return deepcopy(item) if item is not None else None

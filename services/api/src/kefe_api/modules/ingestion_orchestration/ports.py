from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    Proposal,
    ProposalMaterialization,
    ProposalReviewDecision,
    StageExecution,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueQuery,
    ProposalQueueRecord,
)


class IngestionOrchestrationRepository(Protocol):
    def create_or_get_run(self, run: IngestionRun) -> IngestionRun: ...

    def get_run(self, run_id: UUID) -> IngestionRun | None: ...

    def update_run(self, run: IngestionRun) -> None: ...

    def add_stage_execution(self, execution: StageExecution) -> None: ...

    def complete_successful_stage(
        self,
        execution: StageExecution,
        proposals: tuple[Proposal, ...],
    ) -> None: ...

    def list_stage_executions(
        self,
        run_id: UUID,
        *,
        stage_code: str | None = None,
        stage_version: str | None = None,
    ) -> tuple[StageExecution, ...]: ...

    def add_proposal(self, proposal: Proposal) -> None: ...

    def get_proposal(self, proposal_id: UUID) -> Proposal | None: ...

    def list_proposals(self, run_id: UUID) -> tuple[Proposal, ...]: ...

    def list_proposal_queue(
        self,
        query: ProposalQueueQuery,
    ) -> tuple[ProposalQueueRecord, ...]: ...

    def get_proposal_queue_record(
        self,
        proposal_id: UUID,
    ) -> ProposalQueueRecord | None: ...

    def add_review_decision(self, decision: ProposalReviewDecision) -> None: ...

    def get_review_decision(self, proposal_id: UUID) -> ProposalReviewDecision | None: ...

    def add_materialization(self, materialization: ProposalMaterialization) -> None: ...

    def find_materialization(
        self,
        proposal_id: UUID,
        *,
        target_kind: str | None = None,
    ) -> ProposalMaterialization | None: ...


class StageProcessor(Protocol):
    def process(
        self,
        *,
        run: IngestionRun,
        stage_code: str,
        stage_version: str,
        input_hash: str,
    ) -> StageProcessorResult: ...


class ProposalTargetMaterializer(Protocol):
    def materialize(
        self,
        *,
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> tuple[str, UUID]: ...

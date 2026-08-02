from __future__ import annotations

from collections import defaultdict
from heapq import heappop, heappush
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    StageExecution,
    StageOutcome,
)


def order_successful_stage_batch(
    execution: StageExecution,
    proposals: tuple[Proposal, ...],
) -> tuple[Proposal, ...]:
    """Validate one successful stage batch and return dependency-safe stable order."""

    if execution.outcome is not StageOutcome.SUCCEEDED:
        raise ValueError("atomic stage completion requires SUCCEEDED outcome")
    if execution.completed_at is None:
        raise ValueError("successful stage completion requires completed_at")

    by_id: dict[UUID, Proposal] = {}
    original_index: dict[UUID, int] = {}
    for index, proposal in enumerate(proposals):
        if proposal.id in by_id:
            raise ValueError("proposal batch contains duplicate ids")
        if proposal.run_id != execution.run_id:
            raise ValueError("proposal batch contains another run")
        if proposal.stage_execution_id != execution.id:
            raise ValueError("proposal batch references another stage execution")
        by_id[proposal.id] = proposal
        original_index[proposal.id] = index

    indegree = {proposal_id: 0 for proposal_id in by_id}
    children: dict[UUID, list[UUID]] = defaultdict(list)
    for proposal in proposals:
        target_id = proposal.supersedes_proposal_id
        if target_id is None or target_id not in by_id:
            continue
        children[target_id].append(proposal.id)
        indegree[proposal.id] += 1

    ready: list[tuple[int, UUID]] = []
    for proposal_id, degree in indegree.items():
        if degree == 0:
            heappush(ready, (original_index[proposal_id], proposal_id))

    ordered: list[Proposal] = []
    while ready:
        _, proposal_id = heappop(ready)
        ordered.append(by_id[proposal_id])
        for child_id in sorted(children[proposal_id], key=original_index.__getitem__):
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                heappush(ready, (original_index[child_id], child_id))

    if len(ordered) != len(proposals):
        raise ValueError("proposal supersession cycle detected")
    return tuple(ordered)

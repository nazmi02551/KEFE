from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class PerspectiveArchetype(StrEnum):
    NEAR_CONSENSUS = "NEAR_CONSENSUS"
    OPPOSING_PRINCIPLE = "OPPOSING_PRINCIPLE"
    BRIDGE_SYNTHESIS = "BRIDGE_SYNTHESIS"
    ALTERNATIVE_PARADIGM = "ALTERNATIVE_PARADIGM"


@dataclass(frozen=True, slots=True)
class PerspectiveCluster:
    cluster_id: UUID
    case_version_id: UUID
    archetype: PerspectiveArchetype
    core_thesis: str
    argument_count: int
    support_percentage: float


@dataclass(frozen=True, slots=True)
class CaseClusteringResult:
    case_version_id: UUID
    total_arguments: int
    clusters: tuple[PerspectiveCluster, ...]

from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.clustering_models import (
    CaseClusteringResult,
    PerspectiveArchetype,
)
from kefe_api.modules.decision.clustering_service import (
    MultiPartyPerspectiveClusteringService,
)


def test_multi_party_perspective_clustering_calculates_support_percentages() -> None:
    case_version_id = uuid4()
    raw_inputs = [
        {
            "archetype": "NEAR_CONSENSUS",
            "core_thesis": "Güvenlik ve kamu yararı önceliklidir.",
            "argument_count": 600,
        },
        {
            "archetype": "OPPOSING_PRINCIPLE",
            "core_thesis": "Bireysel özgürlük ve mahremiyet pazarlık konusu edilemez.",
            "argument_count": 300,
        },
        {
            "archetype": "BRIDGE_SYNTHESIS",
            "core_thesis": "Kademeli denetim ve bağımsız ombudsman gözetimi ile denge kurulabilir.",
            "argument_count": 100,
        },
    ]

    result = MultiPartyPerspectiveClusteringService.cluster_case_perspectives(
        case_version_id, raw_inputs
    )

    assert isinstance(result, CaseClusteringResult)
    assert result.total_arguments == 1000
    assert len(result.clusters) == 3

    assert result.clusters[0].archetype == PerspectiveArchetype.NEAR_CONSENSUS
    assert result.clusters[0].support_percentage == 60.0

    assert result.clusters[1].archetype == PerspectiveArchetype.OPPOSING_PRINCIPLE
    assert result.clusters[1].support_percentage == 30.0

    assert result.clusters[2].archetype == PerspectiveArchetype.BRIDGE_SYNTHESIS
    assert result.clusters[2].support_percentage == 10.0

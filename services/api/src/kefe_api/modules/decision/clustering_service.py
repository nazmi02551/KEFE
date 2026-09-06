from __future__ import annotations

from uuid import UUID, uuid4

from kefe_api.modules.decision.clustering_models import (
    CaseClusteringResult,
    PerspectiveArchetype,
    PerspectiveCluster,
)


class MultiPartyPerspectiveClusteringService:
    @staticmethod
    def cluster_case_perspectives(
        case_version_id: UUID,
        raw_cluster_inputs: list[dict[str, any]],
    ) -> CaseClusteringResult:
        total_args = sum(int(c.get("argument_count", 0)) for c in raw_cluster_inputs)
        base_total = max(1, total_args)

        clusters: list[PerspectiveCluster] = []
        for inp in raw_cluster_inputs:
            count = int(inp.get("argument_count", 0))
            pct = round((count / base_total) * 100.0, 2) if total_args > 0 else 0.0

            clusters.append(
                PerspectiveCluster(
                    cluster_id=uuid4(),
                    case_version_id=case_version_id,
                    archetype=PerspectiveArchetype(inp["archetype"]),
                    core_thesis=str(inp["core_thesis"]).strip(),
                    argument_count=count,
                    support_percentage=pct,
                )
            )

        # Sort clusters by support percentage descending
        clusters.sort(key=lambda c: c.support_percentage, reverse=True)

        return CaseClusteringResult(
            case_version_id=case_version_id,
            total_arguments=total_args,
            clusters=tuple(clusters),
        )

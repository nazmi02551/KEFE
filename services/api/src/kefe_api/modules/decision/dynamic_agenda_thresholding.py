from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgendaPriorityTier(StrEnum):
    NATIONAL_URGENCY_SPIKE = "NATIONAL_URGENCY_SPIKE"
    REGIONAL_EMERGENT_TOPIC = "REGIONAL_EMERGENT_TOPIC"
    MONITORED_INCUBATION = "MONITORED_INCUBATION"


@dataclass(frozen=True, slots=True)
class DynamicAgendaResult:
    topic_id: str
    topic_title: str
    priority_tier: AgendaPriorityTier
    resonance_velocity_index: float
    viewpoint_diversity_entropy: float
    is_featured_on_national_ballot: bool


class DynamicAgendaThresholdingService:
    @staticmethod
    def evaluate_topic(
        *,
        topic_id: str,
        topic_title: str,
        resonance_velocity_index: float,
        viewpoint_diversity_entropy: float,
    ) -> DynamicAgendaResult:
        if len(topic_title.strip()) < 5:
            raise ValueError("topic_title must have at least 5 characters")
        if not 0.0 <= resonance_velocity_index <= 1.0:
            raise ValueError(f"resonance_velocity_index must be in [0.0, 1.0], got {resonance_velocity_index}")
        if not 0.0 <= viewpoint_diversity_entropy <= 1.0:
            raise ValueError(f"viewpoint_diversity_entropy must be in [0.0, 1.0], got {viewpoint_diversity_entropy}")

        # Determine tier based on velocity and diversity (prevents astroturfing)
        combined_score = 0.6 * resonance_velocity_index + 0.4 * viewpoint_diversity_entropy

        if combined_score >= 0.75:
            tier = AgendaPriorityTier.NATIONAL_URGENCY_SPIKE
            featured = True
        elif combined_score >= 0.45:
            tier = AgendaPriorityTier.REGIONAL_EMERGENT_TOPIC
            featured = False
        else:
            tier = AgendaPriorityTier.MONITORED_INCUBATION
            featured = False

        return DynamicAgendaResult(
            topic_id=topic_id.strip(),
            topic_title=topic_title.strip(),
            priority_tier=tier,
            resonance_velocity_index=round(resonance_velocity_index, 2),
            viewpoint_diversity_entropy=round(viewpoint_diversity_entropy, 2),
            is_featured_on_national_ballot=featured,
        )

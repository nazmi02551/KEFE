from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BotDefenseState(StrEnum):
    ORGANIC_CITIZEN_AUTHENTIC = "ORGANIC_CITIZEN_AUTHENTIC"
    SUSPECTED_BOT_COORDINATION = "SUSPECTED_BOT_COORDINATION"
    ISOLATED_QUARANTINE_SWARM = "ISOLATED_QUARANTINE_SWARM"


@dataclass(frozen=True, slots=True)
class BotShieldResult:
    cluster_id: str
    target_case_id: str
    defense_state: BotDefenseState
    synthetic_probability_score: float
    quarantined_bot_payloads_count: int
    semantic_entropy_index: float


class SyntheticAstroturfingShieldService:
    @staticmethod
    def inspect_cluster(
        *,
        cluster_id: str,
        target_case_id: str,
        synthetic_probability_score: float,
        quarantined_bot_payloads_count: int,
        semantic_entropy_index: float,
    ) -> BotShieldResult:
        if not 0.0 <= synthetic_probability_score <= 1.0:
            raise ValueError(f"synthetic_probability_score must be in [0.0, 1.0], got {synthetic_probability_score}")
        if quarantined_bot_payloads_count < 0:
            raise ValueError("quarantined_bot_payloads_count cannot be negative")
        if not 0.0 <= semantic_entropy_index <= 1.0:
            raise ValueError(f"semantic_entropy_index must be in [0.0, 1.0], got {semantic_entropy_index}")

        # State determination
        if synthetic_probability_score >= 0.80 and semantic_entropy_index < 0.25:
            state = BotDefenseState.ISOLATED_QUARANTINE_SWARM
        elif synthetic_probability_score >= 0.40:
            state = BotDefenseState.SUSPECTED_BOT_COORDINATION
        else:
            state = BotDefenseState.ORGANIC_CITIZEN_AUTHENTIC

        return BotShieldResult(
            cluster_id=cluster_id.strip(),
            target_case_id=target_case_id.strip(),
            defense_state=state,
            synthetic_probability_score=round(synthetic_probability_score, 2),
            quarantined_bot_payloads_count=quarantined_bot_payloads_count,
            semantic_entropy_index=round(semantic_entropy_index, 2),
        )

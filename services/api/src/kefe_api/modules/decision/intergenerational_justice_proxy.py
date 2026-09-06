from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntergenerationalImpactStatus(StrEnum):
    REGENERATIVE_FUTURE_STEWARDSHIP = "REGENERATIVE_FUTURE_STEWARDSHIP"
    TRANSITIONAL_BURDEN_MONITORED = "TRANSITIONAL_BURDEN_MONITORED"
    INTERGENERATIONAL_DEBT_DEPLETION = "INTERGENERATIONAL_DEBT_DEPLETION"


@dataclass(frozen=True, slots=True)
class IntergenerationalJusticeResult:
    proxy_id: str
    policy_domain: str
    impact_status: IntergenerationalImpactStatus
    stewardship_equity_index: float
    planetary_boundary_headroom_score: float


class IntergenerationalJusticeProxyService:
    @staticmethod
    def evaluate_impact(
        *,
        proxy_id: str,
        policy_domain: str,
        stewardship_equity_index: float,
        planetary_boundary_headroom_score: float,
    ) -> IntergenerationalJusticeResult:
        if not 0.0 <= stewardship_equity_index <= 1.0:
            raise ValueError(f"stewardship_equity_index must be in [0.0, 1.0], got {stewardship_equity_index}")
        if not 0.0 <= planetary_boundary_headroom_score <= 1.0:
            raise ValueError(f"planetary_boundary_headroom_score must be in [0.0, 1.0], got {planetary_boundary_headroom_score}")
        if len(policy_domain.strip()) < 3:
            raise ValueError("policy_domain must have at least 3 characters")

        if stewardship_equity_index >= 0.80 and planetary_boundary_headroom_score >= 0.70:
            status = IntergenerationalImpactStatus.REGENERATIVE_FUTURE_STEWARDSHIP
        elif stewardship_equity_index >= 0.40:
            status = IntergenerationalImpactStatus.TRANSITIONAL_BURDEN_MONITORED
        else:
            status = IntergenerationalImpactStatus.INTERGENERATIONAL_DEBT_DEPLETION

        return IntergenerationalJusticeResult(
            proxy_id=proxy_id.strip(),
            policy_domain=policy_domain.strip(),
            impact_status=status,
            stewardship_equity_index=round(stewardship_equity_index, 2),
            planetary_boundary_headroom_score=round(planetary_boundary_headroom_score, 2),
        )

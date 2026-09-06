from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DivergenceClassification(StrEnum):
    BROAD_CONSENSUS = "BROAD_CONSENSUS"
    BIPOLAR_DIVERGENCE = "BIPOLAR_DIVERGENCE"
    FRAGMENTED_PLURALITY = "FRAGMENTED_PLURALITY"
    LEANING_MAJORITY = "LEANING_MAJORITY"


@dataclass(frozen=True, slots=True)
class DivergenceClassificationResult:
    case_version_id: UUID
    distribution: dict[str, float]
    classification: DivergenceClassification
    leading_share: float
    margin_of_divergence: float


class ConsensusDivergenceClassifier:
    @staticmethod
    def classify(
        case_version_id: UUID,
        distribution: dict[str, float],
    ) -> DivergenceClassificationResult:
        if not distribution:
            raise ValueError("distribution must not be empty")

        sorted_shares = sorted(distribution.values(), reverse=True)
        leading = sorted_shares[0]
        second = sorted_shares[1] if len(sorted_shares) > 1 else 0.0
        margin = round(leading - second, 4)

        if leading >= 0.70:
            classification = DivergenceClassification.BROAD_CONSENSUS
        elif len(sorted_shares) >= 2 and (leading + second >= 0.80) and (margin <= 0.15):
            classification = DivergenceClassification.BIPOLAR_DIVERGENCE
        elif leading <= 0.45 and len(sorted_shares) >= 3:
            classification = DivergenceClassification.FRAGMENTED_PLURALITY
        else:
            classification = DivergenceClassification.LEANING_MAJORITY

        return DivergenceClassificationResult(
            case_version_id=case_version_id,
            distribution=distribution,
            classification=classification,
            leading_share=round(leading, 4),
            margin_of_divergence=margin,
        )

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class NormativePhilosophy(StrEnum):
    UTILITARIAN_MAX_WELFARE = "UTILITARIAN_MAX_WELFARE"
    DEONTOLOGICAL_CATEGORICAL_RIGHTS = "DEONTOLOGICAL_CATEGORICAL_RIGHTS"
    RAWLSIAN_MAXIMIN_EQUITY = "RAWLSIAN_MAXIMIN_EQUITY"
    VIRTUE_ETHICS_CHARACTER = "VIRTUE_ETHICS_CHARACTER"


@dataclass(frozen=True, slots=True)
class OptionNormativeEvaluation:
    option_code: str
    utilitarian_score: float
    deontological_score: float
    rawlsian_score: float
    virtue_score: float
    dominant_philosophy: NormativePhilosophy


@dataclass(frozen=True, slots=True)
class CaseNormativeModelResult:
    case_version_id: UUID
    evaluations: tuple[OptionNormativeEvaluation, ...]


class NormativeModelsCalculator:
    @staticmethod
    def evaluate_option(
        option_code: str,
        utilitarian_score: float,
        deontological_score: float,
        rawlsian_score: float,
        virtue_score: float,
    ) -> OptionNormativeEvaluation:
        scores = {
            NormativePhilosophy.UTILITARIAN_MAX_WELFARE: utilitarian_score,
            NormativePhilosophy.DEONTOLOGICAL_CATEGORICAL_RIGHTS: deontological_score,
            NormativePhilosophy.RAWLSIAN_MAXIMIN_EQUITY: rawlsian_score,
            NormativePhilosophy.VIRTUE_ETHICS_CHARACTER: virtue_score,
        }

        for k, v in scores.items():
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"Score for {k} must be in [0.0, 1.0], got {v}")

        dominant = max(scores.items(), key=lambda item: item[1])[0]

        return OptionNormativeEvaluation(
            option_code=option_code.strip(),
            utilitarian_score=round(utilitarian_score, 2),
            deontological_score=round(deontological_score, 2),
            rawlsian_score=round(rawlsian_score, 2),
            virtue_score=round(virtue_score, 2),
            dominant_philosophy=dominant,
        )

    @staticmethod
    def evaluate_case(
        case_version_id: UUID,
        evaluations: list[OptionNormativeEvaluation],
    ) -> CaseNormativeModelResult:
        if not evaluations:
            raise ValueError("Evaluations list must not be empty")
        return CaseNormativeModelResult(
            case_version_id=case_version_id,
            evaluations=tuple(evaluations),
        )

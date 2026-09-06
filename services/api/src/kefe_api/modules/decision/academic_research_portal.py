from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResearchCorpusType(StrEnum):
    DELIBERATIVE_POLARIZATION_DATASET = "DELIBERATIVE_POLARIZATION_DATASET"
    ETHICAL_TRADE_OFF_CORPUS = "ETHICAL_TRADE_OFF_CORPUS"
    ARGUMENT_GRAPH_TOPOLOGY = "ARGUMENT_GRAPH_TOPOLOGY"
    POLICY_OUTCOME_BENCHMARK = "POLICY_OUTCOME_BENCHMARK"


@dataclass(frozen=True, slots=True)
class AcademicResearchDatasetResult:
    dataset_id: str
    dataset_title: str
    corpus_type: ResearchCorpusType
    record_count: int
    differential_privacy_epsilon: float
    doi_identifier: str


class AcademicResearchPortalService:
    @staticmethod
    def publish_or_get_dataset(
        *,
        dataset_id: str,
        dataset_title: str,
        corpus_type: ResearchCorpusType,
        record_count: int,
        differential_privacy_epsilon: float,
        doi_identifier: str,
    ) -> AcademicResearchDatasetResult:
        if len(dataset_title.strip()) < 5:
            raise ValueError("dataset_title must have at least 5 characters")
        if len(doi_identifier.strip()) < 7:
            raise ValueError("doi_identifier must have at least 7 characters")
        if record_count < 0:
            raise ValueError("record_count cannot be negative")
        if not 0.0 <= differential_privacy_epsilon <= 1.0:
            raise ValueError(f"differential_privacy_epsilon must be in [0.0, 1.0], got {differential_privacy_epsilon}")

        return AcademicResearchDatasetResult(
            dataset_id=dataset_id.strip(),
            dataset_title=dataset_title.strip(),
            corpus_type=corpus_type,
            record_count=record_count,
            differential_privacy_epsilon=round(differential_privacy_epsilon, 2),
            doi_identifier=doi_identifier.strip(),
        )

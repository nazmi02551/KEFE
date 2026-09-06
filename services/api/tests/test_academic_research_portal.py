from __future__ import annotations

from kefe_api.modules.decision.academic_research_portal import (
    AcademicResearchDatasetResult,
    AcademicResearchPortalService,
    ResearchCorpusType,
)


def test_academic_research_portal_publishes_dataset() -> None:
    r = AcademicResearchPortalService.publish_or_get_dataset(
        dataset_id="ds_kefe_001",
        dataset_title="Global Civic Deliberation & Bridge Graph 2026",
        corpus_type=ResearchCorpusType.ARGUMENT_GRAPH_TOPOLOGY,
        record_count=125000,
        differential_privacy_epsilon=0.50,
        doi_identifier="10.1000/182_kefe_open_data",
    )

    assert isinstance(r, AcademicResearchDatasetResult)
    assert r.corpus_type == ResearchCorpusType.ARGUMENT_GRAPH_TOPOLOGY
    assert r.record_count == 125000
    assert r.differential_privacy_epsilon == 0.50


def test_academic_research_invalid_epsilon() -> None:
    failed = False
    try:
        AcademicResearchPortalService.publish_or_get_dataset(
            dataset_id="ds_kefe_002",
            dataset_title="Kısa",  # < 5
            corpus_type=ResearchCorpusType.DELIBERATIVE_POLARIZATION_DATASET,
            record_count=100,
            differential_privacy_epsilon=1.50,  # > 1.0
            doi_identifier="10.1000/1",
        )
    except ValueError:
        failed = True

    assert failed is True

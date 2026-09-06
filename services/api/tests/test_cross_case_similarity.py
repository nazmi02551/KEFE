from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.cross_case_similarity import (
    CrossCaseSimilarityCalculator,
    CrossCaseSimilarityResult,
    SimilarityAlignmentTier,
)


def test_cross_case_similarity_calculates_high_analogue() -> None:
    src_id = uuid4()
    tgt_id = uuid4()

    r = CrossCaseSimilarityCalculator.calculate_similarity(
        source_case_id=src_id,
        target_case_id=tgt_id,
        target_case_title="Tarihsel Su Kaynakları Dağıtım Krizi (1994)",
        similarity_score=0.88,
        shared_tension_summary="Sınırlı kamu kaynağının tarımsal ihtiyaçlar ve kentsel tüketim arasındaki adil bölüşümü.",
    )

    assert isinstance(r, CrossCaseSimilarityResult)
    assert r.alignment_tier == SimilarityAlignmentTier.HIGH_TOPOLOGICAL_ANALOGUE
    assert r.similarity_score == 0.88


def test_cross_case_invalid_score() -> None:
    src_id = uuid4()
    tgt_id = uuid4()
    failed = False
    try:
        CrossCaseSimilarityCalculator.calculate_similarity(
            source_case_id=src_id,
            target_case_id=tgt_id,
            target_case_title="Kısa",  # < 5
            similarity_score=1.50,  # > 1.0
            shared_tension_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True

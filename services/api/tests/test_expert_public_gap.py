from __future__ import annotations

import pytest
from kefe_api.modules.decision.expert_public_gap import (
    ExpertPublicGapService,
    GapClassification,
    MIN_EXPERT_SAMPLE_SIZE,
    MIN_PUBLIC_SAMPLE_SIZE,
)


def test_classify_gap_boundaries():
    assert ExpertPublicGapService.classify_gap(5) == GapClassification.CONVERGENT
    assert ExpertPublicGapService.classify_gap(10) == GapClassification.CONVERGENT
    assert ExpertPublicGapService.classify_gap(15) == GapClassification.TECHNICAL_TRANSLATION_GAP
    assert ExpertPublicGapService.classify_gap(25) == GapClassification.TECHNICAL_TRANSLATION_GAP
    assert ExpertPublicGapService.classify_gap(26) == GapClassification.NORMATIVE_VALUE_DIVERGENCE
    assert ExpertPublicGapService.classify_gap(50) == GapClassification.NORMATIVE_VALUE_DIVERGENCE

    # Trust deficit override
    assert (
        ExpertPublicGapService.classify_gap(5, trust_deficit=True)
        == GapClassification.TRUST_DEFICIT_SKEPTICISM
    )


def test_get_gap_analysis_contract_guarantees():
    result = ExpertPublicGapService.get_gap_analysis("case-epg-test")

    assert result.case_version_id == "case-epg-test"
    assert result.expert_sample_size >= MIN_EXPERT_SAMPLE_SIZE
    assert result.public_sample_size >= MIN_PUBLIC_SAMPLE_SIZE

    assert sum(result.expert_distribution.values()) == pytest.approx(1.0, rel=1e-2)
    assert sum(result.public_distribution.values()) == pytest.approx(1.0, rel=1e-2)

    assert 0 <= result.gap_magnitude_points <= 100
    assert result.gap_classification in GapClassification
    assert len(result.key_divergence_drivers) >= 2
    assert len(result.epistemic_bridges) >= 2

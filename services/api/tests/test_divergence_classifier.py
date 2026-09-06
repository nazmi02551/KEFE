from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.divergence_classifier import (
    ConsensusDivergenceClassifier,
    DivergenceClassification,
)


def test_consensus_divergence_classifier_determines_correct_categories() -> None:
    case_id = uuid4()

    # 1. Broad Consensus (78% vs 22%)
    r1 = ConsensusDivergenceClassifier.classify(
        case_id, {"opt_a": 0.78, "opt_b": 0.22}
    )
    assert r1.classification == DivergenceClassification.BROAD_CONSENSUS
    assert r1.leading_share == 0.78

    # 2. Bipolar Divergence (49% vs 46% vs 5%)
    r2 = ConsensusDivergenceClassifier.classify(
        case_id, {"opt_a": 0.49, "opt_b": 0.46, "opt_c": 0.05}
    )
    assert r2.classification == DivergenceClassification.BIPOLAR_DIVERGENCE
    assert r2.margin_of_divergence == 0.03

    # 3. Fragmented Plurality (35% vs 33% vs 32%)
    r3 = ConsensusDivergenceClassifier.classify(
        case_id, {"opt_a": 0.35, "opt_b": 0.33, "opt_c": 0.32}
    )
    assert r3.classification == DivergenceClassification.FRAGMENTED_PLURALITY

    # 4. Leaning Majority (62% vs 38%)
    r4 = ConsensusDivergenceClassifier.classify(
        case_id, {"opt_a": 0.62, "opt_b": 0.38}
    )
    assert r4.classification == DivergenceClassification.LEANING_MAJORITY

from __future__ import annotations

from kefe_api.modules.decision.xai_reasoning_provenance import (
    ReasoningTransparencyTier,
    XaiProvenanceResult,
    XaiReasoningProvenanceService,
)


def test_xai_provenance_generates_full_axiomatic_graph() -> None:
    r = XaiReasoningProvenanceService.generate_provenance_graph(
        provenance_id="xai_001",
        target_synthesis_id="synth_001",
        causal_steps_count=6,
        axiomatic_grounding_score=0.96,
        root_axiom_summary="Anayasal orantılılık ve en az müdahaleci araç ilkesinden türetilmiştir.",
    )

    assert isinstance(r, XaiProvenanceResult)
    assert r.transparency_tier == ReasoningTransparencyTier.FULL_AXIOMATIC_PROVENANCE
    assert r.causal_steps_count == 6
    assert r.axiomatic_grounding_score == 0.96


def test_xai_provenance_invalid_inputs() -> None:
    failed = False
    try:
        XaiReasoningProvenanceService.generate_provenance_graph(
            provenance_id="xai_002",
            target_synthesis_id="s_002",
            causal_steps_count=1,  # < 2
            axiomatic_grounding_score=1.50,  # > 1.0
            root_axiom_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True

from __future__ import annotations

from kefe_api.modules.decision.citizen_jury_chamber import (
    CitizenJuryChamberService,
    CitizenJuryResult,
    CitizenJuryStage,
)


def test_citizen_jury_convenes_and_emits_verdict() -> None:
    r = CitizenJuryChamberService.convene_jury(
        jury_id="jury_001",
        dilemma_title="Yapay Zeka ve Otonom Araçlar Trafik Sorumluluk Düzenlemesi",
        stage=CitizenJuryStage.CONSENSUS_VERDICT_EMITTED,
        juror_count=24,
        expert_witnesses_count=4,
        verdict_consensus_rate=0.88,
    )

    assert isinstance(r, CitizenJuryResult)
    assert r.stage == CitizenJuryStage.CONSENSUS_VERDICT_EMITTED
    assert r.juror_count == 24
    assert r.verdict_consensus_rate == 0.88


def test_citizen_jury_invalid_juror_count() -> None:
    failed = False
    try:
        CitizenJuryChamberService.convene_jury(
            jury_id="jury_002",
            dilemma_title="Kısa",  # < 5
            stage=CitizenJuryStage.STRATIFIED_PANEL_ASSEMBLY,
            juror_count=5,  # < 12
            expert_witnesses_count=0,  # < 1
            verdict_consensus_rate=1.20,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True

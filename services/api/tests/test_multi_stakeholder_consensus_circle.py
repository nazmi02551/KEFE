from __future__ import annotations

from kefe_api.modules.decision.multi_stakeholder_consensus_circle import (
    ConsensusCircleResult,
    ConsensusCircleState,
    MultiStakeholderConsensusCircleService,
)


def test_multi_stakeholder_ratifies_pact() -> None:
    r = MultiStakeholderConsensusCircleService.register_circle(
        circle_id="crc_001",
        pact_title="Sanayi Emisyonları ve Yerel Halk Sağlığı Uzlaşı Sözleşmesi",
        stakeholder_groups_count=4,
        mutual_concession_score=0.85,
        synthesis_covenant_summary="Aşamalı filtreleme yatırımlarına karşılık vergi teşviki ve bağımsız hava izleme istasyonu mutabakatı.",
    )

    assert isinstance(r, ConsensusCircleResult)
    assert r.state == ConsensusCircleState.SYNTHESIS_PACT_RATIFIED
    assert r.stakeholder_groups_count == 4
    assert r.mutual_concession_score == 0.85


def test_multi_stakeholder_invalid_groups() -> None:
    failed = False
    try:
        MultiStakeholderConsensusCircleService.register_circle(
            circle_id="crc_002",
            pact_title="Kısa",  # < 5
            stakeholder_groups_count=1,  # < 2
            mutual_concession_score=1.50,  # > 1.0
            synthesis_covenant_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True

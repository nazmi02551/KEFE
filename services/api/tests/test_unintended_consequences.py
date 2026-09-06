from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.unintended_consequences import (
    ConsequenceSeverity,
    ConsequenceType,
    UnintendedConsequenceItem,
    UnintendedConsequencesCalculator,
    UnintendedConsequencesResult,
)


def test_unintended_consequences_evaluates_systemic_risk() -> None:
    case_id = uuid4()

    items = [
        UnintendedConsequenceItem(
            consequence_type=ConsequenceType.PERVERSE_INCENTIVE,
            severity=ConsequenceSeverity.SEVERE_PARADOX,
            mitigation_feasibility=0.40,
            description="Kira tavan fiyatı uygulaması ev sahiplerinin evleri piyasadan çekmesine neden oldu.",
        ),
        UnintendedConsequenceItem(
            consequence_type=ConsequenceType.BEHAVIORAL_REBOUND,
            severity=ConsequenceSeverity.MODERATE_IMPACT,
            mitigation_feasibility=0.70,
            description="Tasarruflu araçların yaygınlaşması toplam kat edilen mesafeyi artırdı.",
        ),
    ]

    r = UnintendedConsequencesCalculator.simulate(
        case_version_id=case_id,
        option_code="OPT_RENT_CAP",
        consequences=items,
    )

    assert isinstance(r, UnintendedConsequencesResult)
    assert r.overall_systemic_risk == ConsequenceSeverity.SEVERE_PARADOX
    assert len(r.consequences) == 2


def test_unintended_consequences_invalid_feasibility() -> None:
    case_id = uuid4()
    failed = False
    try:
        UnintendedConsequencesCalculator.simulate(
            case_version_id=case_id,
            option_code="OPT_ERR",
            consequences=[
                UnintendedConsequenceItem(
                    consequence_type=ConsequenceType.MARKET_DISTORTION,
                    severity=ConsequenceSeverity.LOW_DRIFT,
                    mitigation_feasibility=1.5,  # > 1.0
                    description="Hata",
                )
            ],
        )
    except ValueError:
        failed = True

    assert failed is True

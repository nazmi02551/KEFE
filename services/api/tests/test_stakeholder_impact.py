from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.stakeholder_impact import (
    StakeholderGroupType,
    StakeholderImpactCalculator,
    StakeholderImpactMatrixResult,
    StakeholderImpactType,
)


def test_stakeholder_impact_calculator_computes_matrix_and_net_score() -> None:
    case_id = uuid4()
    raw_items = [
        {
            "stakeholder_group": "DIRECT_USERS",
            "impact_type": "BENEFIT",
            "impact_score": 4,
            "description": "Gece ulaşım konforu ve erişim artışı.",
        },
        {
            "stakeholder_group": "WORKERS",
            "impact_type": "BURDEN",
            "impact_score": -3,
            "description": "Şoför ve hat görevlilerine gece vardiyası yükü.",
        },
        {
            "stakeholder_group": "TAXPAYERS",
            "impact_type": "BURDEN",
            "impact_score": -2,
            "description": "Belediye bütçesinden ek sübvansiyon ihtiyacı.",
        },
        {
            "stakeholder_group": "VULNERABLE_GROUPS",
            "impact_type": "PROTECTION",
            "impact_score": 5,
            "description": "Gece çalışan dar gelirli vatandaşlara güvenli seyahat.",
        },
    ]

    result = StakeholderImpactCalculator.calculate_matrix(
        case_id,
        "OPTION_EXPAND_NIGHT_TRANSIT",
        raw_items,
    )

    assert isinstance(result, StakeholderImpactMatrixResult)
    assert result.option_code == "OPTION_EXPAND_NIGHT_TRANSIT"
    assert len(result.impact_items) == 4
    # Net score: 4 + (-3) + (-2) + 5 = 4
    assert result.net_equity_score == 4
    assert result.impact_items[0].stakeholder_group == StakeholderGroupType.DIRECT_USERS
    assert result.impact_items[3].impact_type == StakeholderImpactType.PROTECTION

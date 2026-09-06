from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.rights_conflict import (
    RestrictionSeverity,
    RightsCollisionType,
    RightsConflictCalculator,
    RightsConflictResult,
)


def test_rights_conflict_calculator_evaluates_severity() -> None:
    case_id = uuid4()

    # 1. Permissible Restriction
    r1 = RightsConflictCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_DIGITAL_ID",
        collision_type=RightsCollisionType.PRIVACY_VS_SECURITY,
        inalienable_core_score=0.85,
        constitutional_rationale="Veri minimizasyonu ve uçtan uca şifreleme ile mahremiyetin özüne dokunulmamaktadır.",
    )
    assert isinstance(r1, RightsConflictResult)
    assert r1.severity == RestrictionSeverity.PERMISSIBLE_RESTRICTION

    # 2. Unconstitutional Breach
    r2 = RightsConflictCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_TOTAL_SURVEILLANCE",
        collision_type=RightsCollisionType.PRIVACY_VS_SECURITY,
        inalienable_core_score=0.20,
        constitutional_rationale="Mahkeme kararı olmaksızın tüm yurttaşların sürekli izlenmesi hakkın özünü zedeler.",
    )
    assert r2.severity == RestrictionSeverity.UNCONSTITUTIONAL_BREACH


def test_rights_conflict_invalid_core_score() -> None:
    case_id = uuid4()
    failed = False
    try:
        RightsConflictCalculator.evaluate(
            case_version_id=case_id,
            option_code="OPT_ERR",
            collision_type=RightsCollisionType.EXPRESSION_VS_DIGNITY,
            inalienable_core_score=1.2,  # > 1.0
            constitutional_rationale="Açıklama",
        )
    except ValueError:
        failed = True

    assert failed is True

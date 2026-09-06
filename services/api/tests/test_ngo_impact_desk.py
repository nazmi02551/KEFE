from __future__ import annotations

from kefe_api.modules.decision.ngo_impact_desk import (
    NgoAdvocacyDomain,
    NgoImpactDeskResult,
    NgoImpactDeskService,
)


def test_ngo_impact_desk_evaluates_campaign() -> None:
    r = NgoImpactDeskService.evaluate_campaign(
        campaign_id="cmp_ngo_001",
        ngo_name="Temiz Hava ve Yaşam Derneği",
        advocacy_domain=NgoAdvocacyDomain.ENVIRONMENT_AND_CLIMATE,
        citizen_endorsement_count=1000,  # 0.50
        institutional_reforms_achieved=3,  # 3 * 0.15 = 0.45 -> total 0.95
    )

    assert isinstance(r, NgoImpactDeskResult)
    assert r.advocacy_domain == NgoAdvocacyDomain.ENVIRONMENT_AND_CLIMATE
    assert r.advocacy_efficacy_score == 0.95
    assert r.institutional_reforms_achieved == 3


def test_ngo_impact_invalid_name() -> None:
    failed = False
    try:
        NgoImpactDeskService.evaluate_campaign(
            campaign_id="cmp_ngo_002",
            ngo_name="AB",  # < 3
            advocacy_domain=NgoAdvocacyDomain.HUMAN_RIGHTS_AND_JUSTICE,
            citizen_endorsement_count=-5,  # < 0
            institutional_reforms_achieved=0,
        )
    except ValueError:
        failed = True

    assert failed is True

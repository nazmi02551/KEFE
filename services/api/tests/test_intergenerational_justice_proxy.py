from __future__ import annotations

from kefe_api.modules.decision.intergenerational_justice_proxy import (
    IntergenerationalImpactStatus,
    IntergenerationalJusticeProxyService,
    IntergenerationalJusticeResult,
)


def test_intergenerational_evaluates_stewardship() -> None:
    r = IntergenerationalJusticeProxyService.evaluate_impact(
        proxy_id="prx_001",
        policy_domain="Ulusal Su Havzaları ve Yeraltı Akifer Yönetimi",
        stewardship_equity_index=0.91,
        planetary_boundary_headroom_score=0.85,
    )

    assert isinstance(r, IntergenerationalJusticeResult)
    assert r.impact_status == IntergenerationalImpactStatus.REGENERATIVE_FUTURE_STEWARDSHIP
    assert r.stewardship_equity_index == 0.91
    assert r.planetary_boundary_headroom_score == 0.85


def test_intergenerational_invalid_inputs() -> None:
    failed = False
    try:
        IntergenerationalJusticeProxyService.evaluate_impact(
            proxy_id="prx_002",
            policy_domain="Su",  # < 3
            stewardship_equity_index=-0.1,  # < 0.0
            planetary_boundary_headroom_score=1.2,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True

from __future__ import annotations

from kefe_api.modules.decision.municipal_participatory_budgeting import (
    MunicipalBudgetProjectResult,
    MunicipalParticipatoryBudgetingService,
    MunicipalProjectDomain,
)


def test_municipal_budgeting_submits_project() -> None:
    r = MunicipalParticipatoryBudgetingService.submit_project(
        project_id="prj_mun_001",
        municipality_name="Kadıköy Belediyesi",
        project_domain=MunicipalProjectDomain.PARKS_AND_GREEN_SPACES,
        requested_budget_try=2500000,
        citizen_votes_count=4500,
        total_eligible_voters=5000,
    )

    assert isinstance(r, MunicipalBudgetProjectResult)
    assert r.civic_approval_rate == 0.90
    assert r.requested_budget_try == 2500000
    assert r.project_domain == MunicipalProjectDomain.PARKS_AND_GREEN_SPACES


def test_municipal_budgeting_invalid_budget() -> None:
    failed = False
    try:
        MunicipalParticipatoryBudgetingService.submit_project(
            project_id="prj_mun_002",
            municipality_name="AB",  # < 3
            project_domain=MunicipalProjectDomain.DISASTER_RESILIENCE_AND_SAFETY,
            requested_budget_try=500,  # < 1000
            citizen_votes_count=-10,  # < 0
            total_eligible_voters=0,  # <= 0
        )
    except ValueError:
        failed = True

    assert failed is True

from __future__ import annotations

import pytest
from kefe_api.modules.decision.stakeholder_distribution import (
    StakeholderCategory,
    StakeholderDistributionService,
)


def test_calculate_cohesion_boundary_conditions():
    assert StakeholderDistributionService.calculate_cohesion({}) == 0.0
    assert StakeholderDistributionService.calculate_cohesion({"A": 1.0}) == 1.0
    assert StakeholderDistributionService.calculate_cohesion({"A": 0.5, "B": 0.5}) == 0.5


def test_get_stakeholder_distribution_contract_validity():
    result = StakeholderDistributionService.get_stakeholder_distribution("case-test-uuid")

    assert result.case_version_id == "case-test-uuid"
    assert result.total_stakeholders_represented > 0
    assert result.active_categories_count == 5
    assert len(result.stakeholder_distributions) == 5
    assert 0.0 <= result.pluralism_score <= 1.0

    total_shares = sum(d.sample_share for d in result.stakeholder_distributions)
    assert total_shares == pytest.approx(1.0, rel=1e-2)

    valid_categories = {c.value for c in StakeholderCategory}
    for item in result.stakeholder_distributions:
        assert item.category.value in valid_categories
        assert len(item.name) > 0
        assert item.participant_count > 0
        assert 0.0 <= item.sample_share <= 1.0
        assert sum(item.option_shares.values()) == pytest.approx(1.0, rel=1e-2)
        assert item.primary_choice in item.option_shares
        assert 0.0 <= item.cohesion_index <= 1.0
        assert isinstance(item.divergence_from_overall_points, int)

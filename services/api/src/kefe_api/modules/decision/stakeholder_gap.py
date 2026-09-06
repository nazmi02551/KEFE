from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class StakeholderSegmentKey(StrEnum):
    DIRECTLY_AFFECTED = "DIRECTLY_AFFECTED"
    GENERAL_PUBLIC = "GENERAL_PUBLIC"
    DOMAIN_PRACTITIONERS = "DOMAIN_PRACTITIONERS"
    REGIONAL_COMMUNITY = "REGIONAL_COMMUNITY"


MIN_STAKEHOLDER_SAMPLE_SIZE = 30


@dataclass(frozen=True, slots=True)
class StakeholderSegmentGap:
    segment_key: StakeholderSegmentKey
    distributions: Mapping[str, float]
    gap_points: int
    sample_size: int

    def __post_init__(self) -> None:
        if self.sample_size < MIN_STAKEHOLDER_SAMPLE_SIZE:
            raise ValueError(
                f"Stakeholder sample size {self.sample_size} is below minimum privacy threshold {MIN_STAKEHOLDER_SAMPLE_SIZE}"
            )


class StakeholderGapCalculator:
    @staticmethod
    def calculate_gap(
        *,
        overall_distributions: Mapping[str, float],
        segment_distributions: Mapping[str, float],
        sample_size: int,
        segment_key: StakeholderSegmentKey,
        target_option: str,
    ) -> StakeholderSegmentGap:
        if sample_size < MIN_STAKEHOLDER_SAMPLE_SIZE:
            raise ValueError(
                f"Cannot disclose stakeholder gap for n={sample_size} < {MIN_STAKEHOLDER_SAMPLE_SIZE}"
            )

        overall_share = overall_distributions.get(target_option, 0.0)
        segment_share = segment_distributions.get(target_option, 0.0)
        gap_points = round((segment_share - overall_share) * 100)

        return StakeholderSegmentGap(
            segment_key=segment_key,
            distributions=dict(segment_distributions),
            gap_points=gap_points,
            sample_size=sample_size,
        )

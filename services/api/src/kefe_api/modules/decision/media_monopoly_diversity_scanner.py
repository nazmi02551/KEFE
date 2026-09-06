from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MediaPluralismLevel(StrEnum):
    PLURALISTIC_INDEPENDENT_DIVERSE = "PLURALISTIC_INDEPENDENT_DIVERSE"
    CORPORATE_CONGLOMERATE_CONCENTRATION = "CORPORATE_CONGLOMERATE_CONCENTRATION"
    STATE_CONTROLLED_MONOPOLY_ALERT = "STATE_CONTROLLED_MONOPOLY_ALERT"


@dataclass(frozen=True, slots=True)
class MediaDiversityResult:
    scanner_id: str
    topic_cluster: str
    pluralism_level: MediaPluralismLevel
    source_diversity_index: float
    independent_outlets_count: int


class MediaMonopolyDiversityScannerService:
    @staticmethod
    def scan_topic(
        *,
        scanner_id: str,
        topic_cluster: str,
        source_diversity_index: float,
        independent_outlets_count: int,
    ) -> MediaDiversityResult:
        if not 0.0 <= source_diversity_index <= 1.0:
            raise ValueError(f"source_diversity_index must be in [0.0, 1.0], got {source_diversity_index}")
        if independent_outlets_count < 0:
            raise ValueError("independent_outlets_count cannot be negative")
        if len(topic_cluster.strip()) < 4:
            raise ValueError("topic_cluster must have at least 4 characters")

        if source_diversity_index >= 0.80 and independent_outlets_count >= 5:
            level = MediaPluralismLevel.PLURALISTIC_INDEPENDENT_DIVERSE
        elif source_diversity_index >= 0.40:
            level = MediaPluralismLevel.CORPORATE_CONGLOMERATE_CONCENTRATION
        else:
            level = MediaPluralismLevel.STATE_CONTROLLED_MONOPOLY_ALERT

        return MediaDiversityResult(
            scanner_id=scanner_id.strip(),
            topic_cluster=topic_cluster.strip(),
            pluralism_level=level,
            source_diversity_index=round(source_diversity_index, 2),
            independent_outlets_count=independent_outlets_count,
        )

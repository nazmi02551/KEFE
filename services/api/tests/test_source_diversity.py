from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.source_diversity import (
    DiversityLevel,
    SourceDiversityCalculator,
    SourceDiversityResult,
    SourcePluralityCategory,
)


def test_source_diversity_calculator_computes_diversity_levels() -> None:
    case_id = uuid4()

    # 1. High Diversity: 4 sources across 4 distinct categories
    sources_high = [
        SourcePluralityCategory.ACADEMIC_SCIENTIFIC,
        SourcePluralityCategory.OFFICIAL_GOVERNMENT,
        SourcePluralityCategory.CIVIC_INDEPENDENT,
        SourcePluralityCategory.MAINSTREAM_JOURNALISM,
    ]
    r1 = SourceDiversityCalculator.calculate(case_id, sources_high)
    assert isinstance(r1, SourceDiversityResult)
    assert r1.total_sources == 4
    assert r1.diversity_level == DiversityLevel.HIGH_DIVERSITY
    assert len(r1.category_breakdown) == 4

    # 2. Balanced Diversity: 3 sources across 2 categories
    sources_balanced = [
        SourcePluralityCategory.OFFICIAL_GOVERNMENT,
        SourcePluralityCategory.OFFICIAL_GOVERNMENT,
        SourcePluralityCategory.CIVIC_INDEPENDENT,
    ]
    r2 = SourceDiversityCalculator.calculate(case_id, sources_balanced)
    assert r2.diversity_level == DiversityLevel.BALANCED_DIVERSITY

    # 3. Limited Diversity: All sources from single category
    sources_limited = [
        SourcePluralityCategory.MAINSTREAM_JOURNALISM,
        SourcePluralityCategory.MAINSTREAM_JOURNALISM,
    ]
    r3 = SourceDiversityCalculator.calculate(case_id, sources_limited)
    assert r3.diversity_level == DiversityLevel.LIMITED_DIVERSITY

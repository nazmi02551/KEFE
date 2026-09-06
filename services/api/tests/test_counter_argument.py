from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.counter_argument import (
    ArgumentRefutationLink,
    CounterArgumentMapperService,
    RefutationType,
)


def test_counter_argument_mapper_links_rebuttals() -> None:
    service = CounterArgumentMapperService()
    arg1 = uuid4()
    arg2 = uuid4()

    link = service.map_refutation(
        source_argument_id=arg2,
        target_argument_id=arg1,
        refutation_type=RefutationType.DIRECT_EMPIRICAL_REBUTTAL,
        refutation_strength=0.85,
        rebuttal_thesis="2026 yılı TÜİK verilerine göre iddia edilen maliyet artışı gerçekleşmemiştir.",
    )

    assert isinstance(link, ArgumentRefutationLink)
    assert link.refutation_type == RefutationType.DIRECT_EMPIRICAL_REBUTTAL

    rebuttals = service.get_rebuttals_for_target(arg1)
    assert len(rebuttals) == 1
    assert rebuttals[0].refutation_strength == 0.85


def test_counter_argument_self_target_rejected() -> None:
    service = CounterArgumentMapperService()
    arg1 = uuid4()

    failed = False
    try:
        service.map_refutation(
            source_argument_id=arg1,
            target_argument_id=arg1,
            refutation_type=RefutationType.LOGICAL_INVALIDATION,
            refutation_strength=0.5,
            rebuttal_thesis="Kendini çürütemez.",
        )
    except ValueError:
        failed = True

    assert failed is True

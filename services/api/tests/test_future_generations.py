from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.future_generations import (
    FutureGenerationsCalculator,
    FutureGenerationsResult,
    HorizonProjectionItem,
    TimeHorizon,
)


def test_future_generations_calculator_computes_intergenerational_equity() -> None:
    case_id = uuid4()

    projections = [
        HorizonProjectionItem(
            horizon=TimeHorizon.HORIZON_5_YEARS,
            impact_score=0.40,
            summary="Kısa vadede altyapı maliyeti ve uyum süreci.",
        ),
        HorizonProjectionItem(
            horizon=TimeHorizon.HORIZON_20_YEARS,
            impact_score=0.80,
            summary="Genç nesiller için temiz enerji bağımsızlığı.",
        ),
        HorizonProjectionItem(
            horizon=TimeHorizon.HORIZON_50_YEARS,
            impact_score=0.90,
            summary="Karbon emisyonlarının kalıcı olarak sıfırlanması.",
        ),
        HorizonProjectionItem(
            horizon=TimeHorizon.HORIZON_100_YEARS,
            impact_score=0.85,
            summary="Gezegensel ekolojik istikrar.",
        ),
    ]

    r = FutureGenerationsCalculator.calculate(
        case_version_id=case_id,
        option_code="OPT_RENEWABLE",
        projections=projections,
    )

    assert isinstance(r, FutureGenerationsResult)
    assert r.net_intergenerational_score > 0.70
    assert len(r.projections) == 4


def test_future_generations_out_of_bounds() -> None:
    case_id = uuid4()
    failed = False
    try:
        FutureGenerationsCalculator.calculate(
            case_version_id=case_id,
            option_code="OPT_ERR",
            projections=[
                HorizonProjectionItem(
                    horizon=TimeHorizon.HORIZON_5_YEARS,
                    impact_score=2.0,  # > 1.0
                    summary="Hata",
                )
            ],
        )
    except ValueError:
        failed = True

    assert failed is True

from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.historical_retrospective import (
    HistoricalEra,
    HistoricalRetrospectiveEngine,
    HistoricalRetrospectiveResult,
)


def test_historical_retrospective_evaluates_event() -> None:
    case_id = uuid4()

    r = HistoricalRetrospectiveEngine.evaluate(
        retrospective_id="retro_001",
        case_version_id=case_id,
        historical_era=HistoricalEra.TWENTIETH_CENTURY,
        historical_year=1973,
        historical_event_name="1973 Petrol Ambargosu ve Enerji Kısıtlaması",
        actual_historical_decision="Hız sınırı 55 mph'ye düşürüldü ve pazar günleri akaryakıt satışı yasaklandı.",
        historical_consequence_summary="Kısa vadede yakıt tüketimi %7 azaldı, uzun vadede küçük motorlu araç inovasyonu ve alternatif enerji yatırımları hız kazandı.",
    )

    assert isinstance(r, HistoricalRetrospectiveResult)
    assert r.historical_year == 1973
    assert r.historical_era == HistoricalEra.TWENTIETH_CENTURY


def test_historical_retrospective_invalid_input() -> None:
    case_id = uuid4()
    failed = False
    try:
        HistoricalRetrospectiveEngine.evaluate(
            retrospective_id="retro_002",
            case_version_id=case_id,
            historical_era=HistoricalEra.INDUSTRIAL_ERA,
            historical_year=1840,
            historical_event_name="A",  # < 4
            actual_historical_decision="Karar",
            historical_consequence_summary="Sonuç özeti metni.",
        )
    except ValueError:
        failed = True

    assert failed is True

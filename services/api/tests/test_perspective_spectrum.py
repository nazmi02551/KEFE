from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.perspective_spectrum import (
    PerspectiveSpectrumResult,
    PerspectiveSpectrumService,
    PrimaryValueHue,
)


def test_perspective_spectrum_maps_properly() -> None:
    case_id = uuid4()

    r = PerspectiveSpectrumService.map_spectrum(
        spectrum_id="spec_001",
        case_version_id=case_id,
        primary_value_hue=PrimaryValueHue.EQUALITY_AND_CARE,
        argument_resonance_count=450,
        cross_value_bridge_ratio=0.72,
        core_moral_intuition="Kırılgan kesimlerin korunması ve adil fırsat eşitliğinin güvence altına alınması.",
    )

    assert isinstance(r, PerspectiveSpectrumResult)
    assert r.primary_value_hue == PrimaryValueHue.EQUALITY_AND_CARE
    assert r.cross_value_bridge_ratio == 0.72
    assert r.argument_resonance_count == 450


def test_perspective_spectrum_invalid_ratio() -> None:
    case_id = uuid4()
    failed = False
    try:
        PerspectiveSpectrumService.map_spectrum(
            spectrum_id="spec_002",
            case_version_id=case_id,
            primary_value_hue=PrimaryValueHue.AUTONOMY_AND_LIBERTY,
            argument_resonance_count=10,
            cross_value_bridge_ratio=1.50,  # > 1.0
            core_moral_intuition="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True

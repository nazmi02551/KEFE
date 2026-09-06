from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.blind_variants import (
    BlindMode,
    BlindVariantsCalculator,
    BlindVariantsResult,
)


def test_blind_variants_calculator_evaluates_blinded_state() -> None:
    case_id = uuid4()

    r = BlindVariantsCalculator.evaluate(
        case_version_id=case_id,
        blind_mode=BlindMode.ACTOR_BLIND,
        blinded_prompt="Bir kamu görevlisi gizli belgeleri basına sızdırdı. Eylemi meşru mu?",
        real_identity_revealed="Edward Snowden / NSA İzleme Belgeleri (2013)",
        neutrality_score=0.90,
    )

    assert isinstance(r, BlindVariantsResult)
    assert r.blind_mode == BlindMode.ACTOR_BLIND
    assert r.neutrality_score == 0.90


def test_blind_variants_invalid_neutrality() -> None:
    case_id = uuid4()
    failed = False
    try:
        BlindVariantsCalculator.evaluate(
            case_version_id=case_id,
            blind_mode=BlindMode.SOURCE_BLIND,
            blinded_prompt="Açıklama metni.",
            real_identity_revealed="Kaynak",
            neutrality_score=1.5,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True

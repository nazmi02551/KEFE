from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/raw-result-gap-interpretation.v1.json"
CARD = (
    ROOT
    / "apps/mobile/lib/features/decision/presentation/reveal_result_card.dart"
)
TEST = ROOT / "apps/mobile/test/raw_result_gap_interpretation_test.dart"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden behavior: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-RAW-RESULT-GAP-INTERPRETATION-001":
        raise SystemExit("unexpected RAW gap interpretation contract id")

    layers = contract["result_layer_policy"]
    if layers["TRUSTED"]["kefe_gap_interpretation_allowed"] is not True:
        raise SystemExit("TRUSTED must preserve the existing KEFE Gap insight")
    if layers["RAW"]["kefe_gap_interpretation_allowed"] is not False:
        raise SystemExit("RAW must not render KEFE Gap interpretation")
    if layers["UNKNOWN_OR_FUTURE"]["fail_closed"] is not True:
        raise SystemExit("unknown result layers must fail closed")
    if contract["presentation"]["magic_sample_threshold_allowed"] is not False:
        raise SystemExit("this boundary must not invent a sample-size threshold")
    if contract["verification"]["new_dedicated_workflow_allowed"] is not False:
        raise SystemExit("verification must reuse the existing Mobile CI")

    card = CARD.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    require(
        card,
        "final showGapInsight = reveal.layer == 'TRUSTED';",
        where="RevealResultCard",
    )
    require(card, "if (showGapInsight &&", where="RevealResultCard")
    require(card, "_MethodologyNote(reveal: reveal)", where="RevealResultCard")
    require(card, "_RevealDistributionRow(", where="RevealResultCard")

    for layer in ("RAW", "TRUSTED", "EXPERIMENTAL"):
        require(test, f"layer: '{layer}'", where="focused mobile test")
    require(test, "reveal-gap-insight", where="focused mobile test")
    require(test, "Temsiliyet iddiası yok", where="focused mobile test")
    require(test, "Güvenilir örneklem", where="focused mobile test")

    forbid(card, "sampleSize >=", where="RevealResultCard")
    forbid(card, "sampleSize >", where="RevealResultCard")

    print("RAW Result KEFE Gap interpretation boundary: OK")


if __name__ == "__main__":
    main()

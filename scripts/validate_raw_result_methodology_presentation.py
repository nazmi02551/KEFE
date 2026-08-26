from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/raw-result-methodology-presentation.v1.json"
CATALOG = (
    ROOT
    / "apps/mobile/lib/core/localization/result_methodology_string_catalog.dart"
)
RESOLVER = ROOT / "apps/mobile/lib/core/localization/result_methodology_strings.dart"
CARD = ROOT / "apps/mobile/lib/features/decision/presentation/reveal_result_card.dart"
TEST = ROOT / "apps/mobile/test/raw_result_methodology_copy_test.dart"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required boundary: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-RAW-RESULT-METHODOLOGY-PRESENTATION-001":
        raise SystemExit("unexpected RAW result presentation contract id")
    if contract["trusted"]["existing_copy_preserved"] is not True:
        raise SystemExit("TRUSTED copy preservation must remain explicit")
    if contract["raw"]["trusted_sample_label_allowed"] is not False:
        raise SystemExit("RAW must never be labeled as a trusted sample")
    if contract["raw"]["representativeness_disclaimer_required"] is not True:
        raise SystemExit("RAW representativeness disclaimer is required")
    if contract["unknown_layer"]["trusted_default_allowed"] is not False:
        raise SystemExit("unknown layers must not default to TRUSTED")

    catalog = CATALOG.read_text(encoding="utf-8")
    resolver = RESOLVER.read_text(encoding="utf-8")
    card = CARD.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        "Observed committed participation",
        "No representativeness claim",
        "Confidence not assessed",
        "Gözlenen kaydedilmiş katılım",
        "Temsiliyet iddiası yok",
        "Güven düzeyi hesaplanmadı",
    ):
        require(catalog, needle, where="result methodology catalog")

    # Keep this gate resilient to canonical Dart formatter line wrapping while
    # still requiring the TRUSTED path to delegate to InternalAlphaStrings.
    for needle in (
        "if (layer == 'TRUSTED')",
        "InternalAlphaStrings(",
        ").resultMethodology(",
        "if (layer == 'RAW')",
        "'result.raw_methodology'",
        "'result.generic_methodology'",
        "confidence == 'INSUFFICIENT'",
    ):
        require(resolver, needle, where="result methodology resolver")

    require(
        card,
        "strings.resultMethodologyForLayer(",
        where="RevealResultCard",
    )
    require(card, "layer: reveal.layer", where="RevealResultCard")

    for needle in (
        "isNot(contains('Güvenilir örneklem'))",
        "isNot(contains('Trusted sample'))",
        "isNot(contains('INSUFFICIENT'))",
        "layer: 'TRUSTED'",
        "layer: 'EXPERIMENTAL'",
    ):
        require(test, needle, where="RAW methodology copy test")

    print("RAW result methodology presentation contract: OK")


if __name__ == "__main__":
    main()

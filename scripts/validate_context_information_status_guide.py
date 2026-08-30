from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/context-information-status-guide.v1.json"
SUPPORT = ROOT / "apps/mobile/lib/features/context/presentation/context_section_support.dart"
LEGACY = ROOT / "apps/mobile/lib/features/context/presentation/context_section_legacy.dart"
PROGRESSIVE = (
    ROOT / "apps/mobile/lib/features/context/presentation/context_section_progressive.dart"
)
STRINGS = ROOT / "apps/mobile/lib/features/context/presentation/context_journey_strings.dart"
MODEL = ROOT / "apps/mobile/lib/features/context/domain/context_models.dart"
TEST = ROOT / "apps/mobile/test/context_section_test.dart"
FORBIDDEN_WORKFLOW = ROOT / ".github/workflows/context-information-status-guide.yml"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required status-guide boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden status-guide behavior: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-CONTEXT-INFORMATION-STATUS-GUIDE-001":
        raise SystemExit("unexpected Context information-status guide contract id")
    status = contract["information_status"]
    if status["scope"] != "CONTEXT_BLOCK":
        raise SystemExit("information status must remain block-level")
    if status["values"] != ["VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"]:
        raise SystemExit("canonical information-status values changed")
    for false_boundary in (
        "linked_source_status_inferred",
        "truth_score_added",
        "confidence_score_added",
        "editorial_methodology_changed",
    ):
        if status[false_boundary] is not False:
            raise SystemExit(f"{false_boundary} must remain false")

    source = contract["source_preview"]
    if source["published_at_rendered_when_present"] is not True:
        raise SystemExit("existing source publication date must be presented")
    if source["published_at_is_provenance_only"] is not True:
        raise SystemExit("source publication date must remain provenance only")
    if contract["architecture"]["new_feature_workflow_allowed"] is not False:
        raise SystemExit("feature-specific workflow growth must remain disabled")
    if FORBIDDEN_WORKFLOW.exists():
        raise SystemExit("status guide must use existing Mobile CI")

    support = SUPPORT.read_text(encoding="utf-8")
    legacy = LEGACY.read_text(encoding="utf-8")
    progressive = PROGRESSIVE.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    model = MODEL.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        "class _InformationStatusGuide",
        "class _InformationStatusGuideRow",
        "['VERIFIED', 'CLAIMED', 'DISPUTED', 'UNKNOWN']",
        "ValueKey('context-information-status-guide')",
        "contextInformationStatusGuideHelper",
        "contextInformationStatusDescription(status)",
        "ValueKey('context-information-status-${status.toLowerCase()}')",
    ):
        require(support, needle, where="shared Context status guide")
    require(legacy, "const _InformationStatusGuide()", where="legacy Context")
    require(
        progressive,
        "const _InformationStatusGuide()",
        where="progressive Context",
    )

    for needle in (
        "'status.guide.title': 'Bilgi durumları ne anlama geliyor?'",
        "'status.guide.title': 'What do these information states mean?'",
        "bağlı kaynağı ayrıca doğrulamaz",
        "does not independently verify a linked source",
        "'sources.published': 'Yayın tarihi: {date}'",
        "'sources.published': 'Published: {date}'",
    ):
        require(strings, needle, where="Context status-guide localization")

    for needle in (
        "final DateTime? publishedAt;",
        "final String claimStatus;",
    ):
        require(model, needle, where="Context domain model")
    for needle in (
        "contextJourneySourcePublished(publishedAt)",
        "ValueKey('context-source-published-${source.id}')",
    ):
        require(support, needle, where="neutral source micro-preview")
    forbid(support, "truthScore", where="Context presentation")
    forbid(support, "confidenceScore", where="Context presentation")

    for needle in (
        "find.byKey(ValueKey('context-information-status-$status'))",
        "Yayın tarihi: 2026-08-30",
        "What do these information states mean?",
        "source preview omits publication date when absent",
        "TextScaler.linear(1.6)",
    ):
        require(test, needle, where="Context widget tests")

    print("Context information-status guide: OK")


if __name__ == "__main__":
    main()

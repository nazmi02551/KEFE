from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/context-source-trust-presentation.v1.json"
SUPPORT = ROOT / "apps/mobile/lib/features/context/presentation/context_section_support.dart"
LEGACY = ROOT / "apps/mobile/lib/features/context/presentation/context_section_legacy.dart"
PROGRESSIVE = (
    ROOT / "apps/mobile/lib/features/context/presentation/context_section_progressive.dart"
)
STRINGS = ROOT / "apps/mobile/lib/features/context/presentation/context_journey_strings.dart"
MODEL = ROOT / "apps/mobile/lib/features/context/domain/context_models.dart"
TEST = ROOT / "apps/mobile/test/context_section_test.dart"
FORBIDDEN_WORKFLOW = ROOT / ".github/workflows/context-source-trust-presentation.yml"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required trust boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden trust signal: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-CONTEXT-SOURCE-TRUST-PRESENTATION-001":
        raise SystemExit("unexpected Context source trust contract id")
    if contract["semantics"]["source_existence_implies_verified"] is not False:
        raise SystemExit("source existence must not imply verification")
    if contract["semantics"]["claim_status_is_block_level"] is not True:
        raise SystemExit("claim status must remain block-level")
    if contract["presentation"]["unconditional_verified_source_icon_allowed"] is not False:
        raise SystemExit("verified-source iconography must remain forbidden")
    if contract["architecture"]["new_github_actions_workflow_allowed"] is not False:
        raise SystemExit("feature-specific workflow growth must remain disabled")
    if FORBIDDEN_WORKFLOW.exists():
        raise SystemExit("Context source trust slice must use existing Mobile CI")

    support = SUPPORT.read_text(encoding="utf-8")
    legacy = LEGACY.read_text(encoding="utf-8")
    progressive = PROGRESSIVE.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    model = MODEL.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    source_start = support.find("class _ContextSourceTile")
    source_end = support.find("\nclass _CountBadge", source_start)
    if source_start < 0 or source_end < 0:
        raise SystemExit("shared _ContextSourceTile boundary is missing")
    source_tile = support[source_start:source_end]

    for needle in (
        "CaseContextSource source",
        "contextJourneySourceReference",
        "contextSourceKind(source.sourceKind)",
        "Icons.link_rounded",
        "ValueKey('context-source-${source.id}')",
    ):
        require(source_tile, needle, where="shared Context source tile")
    forbid(source_tile, "Icons.verified_outlined", where="shared Context source tile")

    require(legacy, "_ContextSourceTile(", where="legacy Context presentation")
    require(progressive, "_ContextSourceTile(", where="progressive Context presentation")
    require(
        progressive,
        "ContextJourneyLayer.sources => Icons.link_rounded",
        where="progressive Context layer icon",
    )
    forbid(
        progressive,
        "ContextJourneyLayer.sources => Icons.verified_outlined",
        where="progressive Context layer icon",
    )

    for needle in (
        "'sources.reference': 'Kaynak kaydı'",
        "'sources.reference': 'Source reference'",
        "contextJourneySourceReference",
    ):
        require(strings, needle, where="Context journey localization")

    for needle in (
        "final String claimStatus;",
        "final List<String> sourceIds;",
        "final String sourceKind;",
        "final Uri? url;",
    ):
        require(model, needle, where="Context domain model")
    forbid(model, "final bool verified;", where="Context source model")
    forbid(model, "final String verificationStatus;", where="Context source model")

    for needle in (
        "expect(find.text('Doğrulandı'), findsOneWidget)",
        "Kaynak kaydı · KEFE Editorial · Editoryal kaynak",
        "expect(find.byIcon(Icons.verified_outlined), findsNothing)",
        "context-source-source-1",
    ):
        require(test, needle, where="Context presentation widget tests")

    print("Context source trust presentation: OK")


if __name__ == "__main__":
    main()

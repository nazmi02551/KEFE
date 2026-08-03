from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PREVIEW_MAIN = ROOT / "apps/mobile/lib/main_preview.dart"
PRODUCTION_MAIN = ROOT / "apps/mobile/lib/main.dart"
MVP_WORKFLOW = ROOT / ".github/workflows/mvp-beta-gates.yml"
GLOBAL_WORKFLOW = ROOT / ".github/workflows/global-readiness.yml"
ADR = (
    ROOT
    / "docs/adr/0090-installable-phone-preview-and-unconfigured-production-shell-boundary.md"
)
CONTRACT = ROOT / "docs/contracts/installable-phone-preview-hotfix.v1.json"
DEDICATED_WORKFLOW = ROOT / ".github/workflows/phone-artifact-boundary-ci.yml"


def fail(message: str) -> None:
    raise SystemExit(message)


def require(source: str, fragment: str, message: str) -> None:
    if fragment not in source:
        fail(message)


def forbid(source: str, fragment: str, message: str) -> None:
    if fragment in source:
        fail(message)


def main() -> None:
    required_files = (
        PREVIEW_MAIN,
        PRODUCTION_MAIN,
        MVP_WORKFLOW,
        GLOBAL_WORKFLOW,
        ADR,
        CONTRACT,
        DEDICATED_WORKFLOW,
    )
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    if missing:
        fail(f"missing installable phone artifact files: {missing}")

    preview = PREVIEW_MAIN.read_text(encoding="utf-8")
    production = PRODUCTION_MAIN.read_text(encoding="utf-8")
    mvp = MVP_WORKFLOW.read_text(encoding="utf-8")
    global_workflow = GLOBAL_WORKFLOW.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    dedicated = DEDICATED_WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "installable-phone-preview-hotfix":
        fail("phone artifact contract identity drifted")
    if contract.get("status") != "accepted":
        fail("phone artifact contract is not accepted")

    production_contract = contract.get("production_entry", {})
    if production_contract != {
        "entrypoint": "lib/main.dart",
        "placeholder_endpoint": "https://beta-api.invalid/",
        "compile_proof_required": True,
        "apk_uploaded": False,
        "preview_fallback": False,
    }:
        fail("production-entry artifact contract drifted")

    preview_contract = contract.get("installable_phone_preview", {})
    if preview_contract != {
        "entrypoint": "lib/main_preview.dart",
        "workflow_artifact_name": "kefe-installable-phone-preview",
        "apk_filename_prefix": "KEFE-phone-preview-",
        "candidate_sha_in_filename": True,
        "decision_repository": "PreviewJourneyDecisionRepository",
        "decision_draft_store": "MemoryDecisionDraftStore",
        "network_required_for_first_weighing": False,
    }:
        fail("installable preview artifact contract drifted")

    for fragment in (
        "features/decision/data/decision_draft_store.dart",
        "PreviewJourneyDecisionRepository()",
        "decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore())",
        "MemoryOnboardingStore()",
        "ProductPreviewApp()",
    ):
        require(preview, fragment, f"preview composition missing: {fragment}")

    for forbidden in (
        "PreviewJourneyDecisionRepository",
        "MemoryDecisionDraftStore",
        "ProductPreviewApp",
        "preview_decision_repository",
        "preview_journey_decision_repository",
    ):
        forbid(production, forbidden, f"preview implementation leaked into production: {forbidden}")

    for fragment in (
        "Build non-installable production shell compile proof",
        "flutter build apk --debug",
        "-t lib/main.dart",
        "--dart-define=KEFE_API_BASE_URL=https://beta-api.invalid/",
        "Production shell APK is intentionally not uploaded",
        "python tool/check_installable_phone_artifact_boundary.py",
    ):
        require(mvp, fragment, f"MVP workflow missing boundary: {fragment}")

    for forbidden in (
        "name: kefe-mvp-beta-internal",
        "path: apps/mobile/build/app/outputs/flutter-apk/app-debug.apk",
        "Upload internal MVP candidate",
    ):
        forbid(mvp, forbidden, f"unconfigured production APK is still published: {forbidden}")

    for fragment in (
        "python tool/check_installable_phone_artifact_boundary.py",
        "flutter build apk --debug -t lib/main_preview.dart",
        "build/phone-preview/KEFE-phone-preview-${CANDIDATE_SHA}.apk",
        "name: kefe-installable-phone-preview",
        "path: apps/mobile/build/phone-preview/KEFE-phone-preview-*.apk",
    ):
        require(global_workflow, fragment, f"Global workflow missing preview artifact boundary: {fragment}")

    for phrase in (
        "Exactly one installable phone-test artifact",
        "Production-entry build remains compile proof only",
        "Preview draft state is process-local",
        "No preview fallback in production",
    ):
        require(adr, phrase, f"ADR-0090 missing decision text: {phrase}")

    for phrase in (
        "Phone artifact boundary contract",
        "check_installable_phone_artifact_boundary.py",
    ):
        require(dedicated, phrase, f"dedicated phone artifact CI missing: {phrase}")

    print("installable phone artifact boundary: PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/connected-alpha-mobile-runtime.v1.json"
APP_CONFIG = ROOT / "apps/mobile/lib/core/config/app_config.dart"
ALPHA_ENTRY = ROOT / "apps/mobile/lib/main_connected_alpha.dart"
PREVIEW_ENTRY = ROOT / "apps/mobile/lib/main_preview.dart"
WORKFLOW = ROOT / ".github/workflows/connected-alpha-mobile-runtime.yml"


def require(text: str, needle: str, *, source: Path) -> None:
    if needle not in text:
        raise SystemExit(f"missing required boundary in {source}: {needle}")


def forbid(text: str, needle: str, *, source: Path) -> None:
    if needle in text:
        raise SystemExit(f"forbidden boundary in {source}: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-CONNECTED-ALPHA-MOBILE-RUNTIME-001":
        raise SystemExit("unexpected connected-alpha contract id")
    if contract["status"] != "MOBILE_BOUNDARY_PREPARED":
        raise SystemExit("unexpected connected-alpha contract status")
    if contract["artifact_policy"]["artifact_upload_before_real_endpoint_allowed"]:
        raise SystemExit("artifact upload must remain blocked before a real endpoint")
    if contract["composition"]["product_preview_fallback_allowed"]:
        raise SystemExit("Product Preview fallback must remain forbidden")

    app_config = APP_CONFIG.read_text(encoding="utf-8")
    for needle in (
        "factory AppConfig.connectedAlphaFromEnvironment()",
        "factory AppConfig.connectedAlpha(",
        "uri.scheme.toLowerCase() != 'https'",
        "InternetAddress.tryParse(host)",
        "host == '10.0.2.2'",
        "host.endsWith('.invalid')",
        "timeoutSeconds < 3 || timeoutSeconds > 60",
    ):
        require(app_config, needle, source=APP_CONFIG)

    alpha_entry = ALPHA_ENTRY.read_text(encoding="utf-8")
    for needle in (
        "AppConfig.connectedAlphaFromEnvironment()",
        "appConfigProvider.overrideWithValue(appConfig)",
        "HttpReflectionDecisionRepository",
        "child: const KefeApp()",
    ):
        require(alpha_entry, needle, source=ALPHA_ENTRY)
    for needle in (
        "ProductPreview",
        "PreviewJourneyDecisionRepository",
        "PreviewAccountRepository",
        "PreviewPrivacyRepository",
        "PreviewProgressRepository",
        "MemoryDecisionDraftStore",
        "MemoryOnboardingStore",
    ):
        forbid(alpha_entry, needle, source=ALPHA_ENTRY)

    preview_entry = PREVIEW_ENTRY.read_text(encoding="utf-8")
    for needle in (
        "ProductPreviewApp",
        "PreviewJourneyDecisionRepository",
        "MemoryDecisionDraftStore",
        "productPreviewVisualModeProvider.overrideWithValue(true)",
    ):
        require(preview_entry, needle, source=PREVIEW_ENTRY)

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(workflow, "main_connected_alpha.dart", source=WORKFLOW)
    require(workflow, "connected_alpha_app_config_test.dart", source=WORKFLOW)
    forbid(workflow, "upload-artifact", source=WORKFLOW)
    forbid(workflow, "actions/upload-artifact", source=WORKFLOW)

    print("connected-alpha mobile runtime contract: OK")


if __name__ == "__main__":
    main()

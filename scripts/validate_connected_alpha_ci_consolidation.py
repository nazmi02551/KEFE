from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/connected-alpha-ci-consolidation.v1.json"
API_CI = ROOT / ".github/workflows/api-ci.yml"
MOBILE_CI = ROOT / ".github/workflows/mobile-ci.yml"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required consolidated evidence: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-CONNECTED-ALPHA-CI-CONSOLIDATION-001":
        raise SystemExit("unexpected Connected Alpha CI consolidation contract id")

    for raw_path in contract["dedicated_workflows_forbidden"]:
        path = ROOT / raw_path
        if path.exists():
            raise SystemExit(f"dedicated Connected Alpha workflow must be removed: {raw_path}")

    api_ci = API_CI.read_text(encoding="utf-8")
    mobile_ci = MOBILE_CI.read_text(encoding="utf-8")

    for needle in (
        "cancel-in-progress: true",
        "check_production_api_runtime.py",
        "docker build --tag kefe-api:ci",
        "from kefe_api.main import app; assert app.title == 'KEFE API'",
        "validate_connected_alpha_schema_snapshot.py",
        "alembic upgrade head --sql",
        "kefe-connected-alpha-schema-snapshot",
        "check_live_raw_collective_result.py",
        "test_live_raw_collective_result_postgres.py",
        "check_connected_alpha_external_acceptance.py",
        "test_connected_alpha_acceptance_tool.py",
        'test -z "${KEFE_CONNECTED_ALPHA_BASE_URL:-}"',
        'test -z "${KEFE_CONNECTED_ALPHA_CASE_ID:-}"',
    ):
        require(api_ci, needle, where="API CI")

    for needle in (
        "cancel-in-progress: true",
        "validate_connected_alpha_mobile_runtime.py",
        "validate_raw_result_methodology_presentation.py",
        "validate_raw_result_gap_interpretation.py",
        "main_connected_alpha.dart",
        "https://alpha-build-proof.example.com",
        "rm -f build/app/outputs/flutter-apk/app-debug.apk",
        "main_preview.dart",
        "kefe-preview-android",
    ):
        require(mobile_ci, needle, where="Mobile CI")

    if contract["run_control"]["new_feature_specific_workflow_allowed"] is not False:
        raise SystemExit("feature-specific workflow growth must remain disabled")
    if contract["evidence_boundaries"]["ci_is_deployed_evidence"] is not False:
        raise SystemExit("CI must not become deployed evidence")
    if contract["evidence_boundaries"]["external_acceptance_ci_may_write_remote"] is not False:
        raise SystemExit("CI must not execute remote Connected Alpha acceptance writes")

    print("Connected Alpha CI consolidation: OK")


if __name__ == "__main__":
    main()

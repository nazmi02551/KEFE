from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def test_decision_revision_contracts_are_final_and_strict() -> None:
    openapi = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    checker = (
        REPO_ROOT / "services" / "api" / "tools" / "check_contract_sync.py"
    ).read_text(encoding="utf-8")
    api_ci = (WORKFLOWS / "api-ci.yml").read_text(encoding="utf-8")

    assert openapi["info"]["version"] == "0.15.0"
    assert "/v1/weigh-sessions/{session_id}/lineage" in openapi["paths"]
    assert (
        "/v1/weigh-sessions/{session_id}/decision-steps/{step_code}/commit"
        in openapi["paths"]
    )
    assert (
        "/v1/weigh-sessions/{session_id}/flow-steps/{step_code}/exposures"
        in openapi["paths"]
    )

    # The global manifest may advance after M2. This test owns only the M2
    # contract registrations and must not pin later architecture slices to 1.29.0.
    assert (
        "- id: openapi\n    path: docs/contracts/openapi.v1.json\n    version: 0.15.0"
        in manifest
    )
    assert (
        "- id: mobile-flow-runtime-ui\n"
        "    path: docs/contracts/mobile-flow-runtime-ui.v1.yaml\n"
        "    version: 1.1.0"
        in manifest
    )
    assert (
        "- id: decision-revision-lineage\n"
        "    path: docs/contracts/decision-revision-lineage.v1.yaml\n"
        "    version: 1.1.0"
        in manifest
    )

    assert "0.15.0" in checker
    assert "0.14.0" not in checker

    assert "contents: read" in api_ci
    assert "sync-draft-contracts:" not in api_ci
    assert "OpenAPI drift gate" in api_ci
    assert "OpenAPI drift diagnostic while draft" not in api_ci

    assert not (WORKFLOWS / "dev-sync-decision-revision.yml").exists()
    assert not (WORKFLOWS / "finalize-pr60-contracts.yml").exists()

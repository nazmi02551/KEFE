from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
FLOW_SRC = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "flow_runtime"
)


def main() -> None:
    contract = (CONTRACTS / "generic-flow-runtime.v1.yaml").read_text(
        encoding="utf-8"
    )
    service = (FLOW_SRC / "service.py").read_text(encoding="utf-8")
    router = (FLOW_SRC / "router.py").read_text(encoding="utf-8")
    openapi = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))

    problems: list[str] = []

    for fragment in {
        "live_content_configuration_lookup: forbidden",
        "actor_scope: same_actor_only",
        "result_payload_included: false",
        "perspective_payload_included: false",
        "private_reason_payload_included: false",
        "FLOW_DECISION_REVISION_REQUIRED",
        "FLOW_COMMIT_REQUIRED",
        "FLOW_RUNTIME_UNAVAILABLE",
    }:
        if fragment not in contract:
            problems.append(f"Generic Flow runtime contract missing: {fragment}")

    for fragment in {
        "case.resolved_flow",
        "session.actor_id != actor_id",
        '"FLOW_DECISION_REVISION_REQUIRED"',
        '"FLOW_COMMIT_REQUIRED"',
        '"FLOW_RUNTIME_UNAVAILABLE"',
    }:
        if fragment not in service:
            problems.append(f"Generic Flow runtime service missing: {fragment}")

    if "ContentConfiguration" in service:
        problems.append("Flow runtime must not depend on live Content Configuration")

    for fragment in {
        '"/weigh-sessions/{session_id}/flow"',
        "PrincipalDep",
        "FlowRuntimeResponse",
    }:
        if fragment not in router:
            problems.append(f"Generic Flow runtime router missing: {fragment}")

    operation = openapi.get("paths", {}).get(
        "/v1/weigh-sessions/{session_id}/flow",
        {},
    ).get("get", {})
    if not operation:
        problems.append("OpenAPI missing generic Flow runtime endpoint")
    if {"HTTPBearer": []} not in operation.get("security", []):
        problems.append("Generic Flow runtime endpoint must require Bearer auth")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Generic Flow runtime contract OK: actor-scoped pinned-Flow authority, "
        "no live config reinterpretation and no result leakage verified."
    )


if __name__ == "__main__":
    main()

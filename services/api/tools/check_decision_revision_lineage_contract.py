from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
ADRS = REPO_ROOT / "docs" / "adr"


def main() -> None:
    contract = (CONTRACTS / "decision-revision-lineage.v1.yaml").read_text(
        encoding="utf-8"
    )
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    erd = (CONTRACTS / "core-erd.v2.mmd").read_text(encoding="utf-8")
    adr = (
        ADRS / "0025-decision-revision-exposure-intervention-delta.md"
    ).read_text(encoding="utf-8")

    problems: list[str] = []

    for fragment in {
        "contract_version: 1.1.0",
        "status: implementation_contract",
        "initial_commit_materializes_revision_one: true",
        "later_decision_reopens_initial_response_rows: false",
        "same_case_question_schema_reused_for_each_decision_step: true",
        "context_fetch_alone_counts_as_exposure: false",
        "not_every_exposure_is_intervention: true",
        "dimension_specific_delta_engines_forbidden: true",
        "claims_causality: false",
        "advocacy_support_is_decision_revision_class: false",
        "path: /v1/weigh-sessions/{session_id}/lineage",
        "target_flow: PRINCIPLE_CONTEXT_RETEST",
        "runtime_case_type_branching: forbidden",
    }:
        if fragment not in contract:
            problems.append(f"Decision revision contract missing: {fragment}")

    for fragment in {
        "DecisionRevision",
        "Exposure",
        "Intervention",
        "DecisionDelta",
        "initial Commit",
        "PRINCIPLE_CONTEXT_RETEST",
        "Dimension-specific delta engines",
    }:
        if fragment not in adr:
            problems.append(f"ADR-0025 missing locked semantic: {fragment}")

    for fragment in {
        "WEIGH_SESSION ||--o{ DECISION_REVISION : contains",
        "WEIGH_SESSION ||--o{ EXPOSURE : records",
        "WEIGH_SESSION ||--o{ INTERVENTION : analyzes",
        "EXPOSURE ||--o| INTERVENTION : may_define",
        "DECISION_REVISION ||--o{ DECISION_DELTA : from",
        "DECISION_REVISION ||--o{ DECISION_DELTA : to",
    }:
        if fragment not in erd:
            problems.append(f"Core ERD v2 missing lineage relation: {fragment}")

    for fragment in {
        "manifest_version: 1.28.0",
        "path: docs/contracts/core-erd.v2.mmd",
        "id: mobile-flow-runtime-ui",
        "path: docs/contracts/mobile-flow-runtime-ui.v1.yaml",
        "id: decision-revision-lineage",
        "path: docs/contracts/decision-revision-lineage.v1.yaml",
        "version: 1.1.0",
        "docs/adr/0024-flutter-flow-driven-consumer-rendering.md",
        "docs/adr/0025-decision-revision-exposure-intervention-delta.md",
    }:
        if fragment not in manifest:
            problems.append(f"Contract manifest missing: {fragment}")

    forbidden = {
        "ActorDelta",
        "LegalDelta",
        "AgeDelta",
        "CostDelta",
    }
    for name in forbidden:
        if f"{name} or" not in adr and f"{name}," not in adr:
            problems.append(f"ADR-0025 must explicitly prohibit dimension engine {name}")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "DecisionRevision lineage v1.1 contract OK: immutable revisions, actual Exposure, "
        "server-validated Intervention, generic non-causal Delta and actor-scoped HTTP are locked."
    )


if __name__ == "__main__":
    main()

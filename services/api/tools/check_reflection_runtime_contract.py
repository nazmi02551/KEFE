from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
ADRS = REPO_ROOT / "docs" / "adr"
FLOW_RUNTIME = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "flow_runtime"
    / "service.py"
)


def main() -> None:
    contract = (CONTRACTS / "reflection-runtime.v1.yaml").read_text(encoding="utf-8")
    adr = (ADRS / "0026-generic-reflection-runtime.md").read_text(encoding="utf-8")
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    flow_runtime = FLOW_RUNTIME.read_text(encoding="utf-8")

    problems: list[str] = []

    for fragment in {
        "contract_version: 1.0.0",
        "creates_decision_revision: false",
        "creates_intervention_by_default: false",
        "causal_claims: forbidden",
        "entity: ReflectionCompletion",
        "later_revision_reopens_reflection: true",
        "collective_result_sample_input: false",
        "signal_qualification_input: false",
        "path: /v1/weigh-sessions/{session_id}/reflection-steps/{step_code}",
        "path: /v1/weigh-sessions/{session_id}/reflection-steps/{step_code}/complete",
        "flow_template: PRINCIPLE_CONTEXT_RETEST",
        "fixed_case_reflection_screen: forbidden",
    }:
        if fragment not in contract:
            problems.append(f"Reflection runtime contract missing: {fragment}")

    for fragment in {
        "Reflection does not create a DecisionRevision",
        "server-derived and non-causal",
        "ReflectionCompletion",
        "Completion is lineage-cursor aware",
        "Reflection is not Exposure or Intervention by default",
        "Reflection is not Signal or Advocacy",
        "Flutter remains Flow-driven",
    }:
        if fragment not in adr:
            problems.append(f"ADR-0026 missing locked semantic: {fragment}")

    for fragment in {
        "id: reflection-runtime",
        "path: docs/contracts/reflection-runtime.v1.yaml",
        "docs/adr/0026-generic-reflection-runtime.md",
    }:
        if fragment not in manifest:
            problems.append(f"Contract manifest missing Reflection registration: {fragment}")

    # Architecture stage invariant: implementation remains explicitly pending until
    # the ADR/contract package is merged and a separate implementation PR begins.
    if "FLOW_REFLECTION_RUNTIME_PENDING" not in flow_runtime:
        problems.append(
            "Architecture PR must not silently replace the pending Reflection runtime boundary"
        )

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Reflection runtime architecture contract OK: actor-scoped non-causal read model, "
        "immutable lineage-cursor completion and case-agnostic Flutter boundary are locked."
    )


if __name__ == "__main__":
    main()

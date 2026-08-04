from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
ADRS = REPO_ROOT / "docs" / "adr"
API_SRC = REPO_ROOT / "services" / "api" / "src" / "kefe_api"


def main() -> None:
    contract = (CONTRACTS / "reflection-runtime.v1.yaml").read_text(encoding="utf-8")
    adr = (ADRS / "0026-generic-reflection-runtime.md").read_text(encoding="utf-8")
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    flow_runtime = (API_SRC / "modules" / "flow_runtime" / "service.py").read_text(encoding="utf-8")
    reflection_service = (API_SRC / "modules" / "decision" / "reflection_service.py").read_text(
        encoding="utf-8"
    )
    reflection_router = (API_SRC / "modules" / "decision" / "reflection_router.py").read_text(
        encoding="utf-8"
    )

    problems: list[str] = []

    for fragment in {
        "contract_version: 1.1.0",
        "status: implementation_contract",
        "creates_decision_revision: false",
        "creates_intervention_by_default: false",
        "causal_claims: forbidden",
        "entity: ReflectionCompletion",
        "durable_postgres: true",
        "later_revision_reopens_reflection: true",
        "collective_result_sample_input: false",
        "signal_qualification_input: false",
        "api_version: 0.16.0",
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

    if "FLOW_REFLECTION_RUNTIME_PENDING" in flow_runtime:
        problems.append("Reflection implementation must remove the pending runtime boundary")
    for fragment in {
        'if step.primitive_code == "REFLECTION"',
        "current_reflection_step_codes",
        "FlowStepRuntimeState.COMPLETED",
        "FlowStepRuntimeState.READY",
    }:
        if fragment not in flow_runtime:
            problems.append(f"Flow runtime missing Reflection implementation: {fragment}")

    for fragment in {
        "class ReflectionService",
        "decision_changed=changed_count > 0",
        "list_reflection_completions",
        "complete_reflection",
    }:
        if fragment not in reflection_service:
            problems.append(f"Reflection service missing implementation semantic: {fragment}")

    for fragment in {
        "/weigh-sessions/{session_id}/reflection-steps/{step_code}",
        "/weigh-sessions/{session_id}/reflection-steps/{step_code}/complete",
        "Idempotency-Key",
    }:
        if fragment not in reflection_router:
            problems.append(f"Reflection HTTP surface missing: {fragment}")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Reflection runtime v1.1 contract OK: non-causal actor-scoped read model, "
        "immutable cursor-pinned completion and generic Flow execution are implemented."
    )


if __name__ == "__main__":
    main()

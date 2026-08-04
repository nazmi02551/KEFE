#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/contracts/foundation-completion-program.v1.json"
PORTFOLIO = ROOT / "docs/roadmap/capability-portfolio.v1.tsv"
REGISTRY = ROOT / "docs/status/active-delivery-registry.v1.json"

REQUIRED_WAVES = {f"F{index}" for index in range(8)}
FORBIDDEN_PROMOTED_STATUSES = {
    "PROPOSAL_REVIEW",
    "TEST",
    "VALIDATION_REQUIRED",
    "VALIDATION_ONLY",
}
CANONICAL_RUNTIME_SHA = "140960ac80881faec5841008eac9444ab67d9b7a"


def fail(message: str) -> None:
    raise SystemExit(f"foundation completion validation failed: {message}")


def load_portfolio() -> dict[str, dict[str, str]]:
    with PORTFOLIO.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        fail("capability portfolio is empty")
    return {row["id"]: row for row in rows}


def main() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    portfolio = load_portfolio()

    waves = program.get("waves", [])
    wave_ids = [wave.get("id") for wave in waves]
    if set(wave_ids) != REQUIRED_WAVES or len(wave_ids) != len(REQUIRED_WAVES):
        fail(f"waves must be exactly {sorted(REQUIRED_WAVES)}")
    wave_by_id = {wave["id"]: wave for wave in waves}

    authority = program.get("authority", {})
    if not authority.get("does_not_promote_working_to_current"):
        fail("WORKING/CURRENT authority boundary must remain explicit")
    if not authority.get("does_not_promote_proposals_or_tests"):
        fail("proposal/test promotion guard must remain enabled")
    if authority.get("delivery_registry") != "docs/status/active-delivery-registry.v1.json":
        fail("foundation program must bind the canonical delivery registry")

    seen_caps: set[str] = set()
    for wave in waves:
        if not wave.get("goal") and wave["id"] == "F0":
            fail("F0 must define a goal")
        criteria = wave.get("exit_criteria", [])
        if not criteria or len(criteria) != len(set(criteria)):
            fail(f"{wave['id']} must have unique exit criteria")
        for dependency in wave.get("depends_on", []):
            if dependency not in REQUIRED_WAVES:
                fail(f"{wave['id']} has unknown dependency {dependency}")
        for cap_id in wave.get("capabilities", []):
            if cap_id not in portfolio:
                fail(f"{wave['id']} references unknown capability {cap_id}")
            seen_caps.add(cap_id)

    mandatory = {
        "CAP-055",
        "CAP-062",
        "CAP-063",
        "CAP-064",
        "CAP-065",
        "CAP-073",
        "CAP-084",
        "CAP-085",
        "CAP-095",
        "CAP-104",
        "CAP-114",
        "CAP-115",
        "CAP-116",
        "CAP-117",
        "CAP-124",
        "CAP-042",
        "CAP-043",
        "CAP-046",
        "CAP-047",
        "CAP-049",
        "CAP-054",
    }
    missing = sorted(mandatory - seen_caps)
    if missing:
        fail(f"mandatory foundation capabilities missing: {missing}")

    f0 = wave_by_id["F0"]
    if f0.get("status") != "COMPLETE_VERIFIED":
        fail("F0 must be COMPLETE_VERIFIED after canonical convergence")
    evidence = f0.get("evidence", {})
    if evidence.get("canonical_runtime_sha") != CANONICAL_RUNTIME_SHA:
        fail("F0 evidence must point to the canonical Admin review runtime")
    required_f0 = {
        "CAPABILITY_PORTFOLIO_PASS",
        "FOUNDATION_COMPLETION_PASS",
        "FULL_VISION_DELIVERY_CONVERGENCE_PASS",
    }
    if not required_f0.issubset(set(evidence.get("validators", []))):
        fail("F0 validator evidence is incomplete")
    required_runtime = {
        "API_CI_PASS",
        "MOBILE_CI_PASS",
        "MVP_BETA_GATES_PASS",
        "GLOBAL_READINESS_PASS",
    }
    if not required_runtime.issubset(set(evidence.get("runtime_workflows", []))):
        fail("F0 runtime workflow evidence is incomplete")

    f1 = wave_by_id["F1"]
    if f1.get("status") != "IN_PROGRESS":
        fail("F1 must remain IN_PROGRESS until public-feed convergence and external gates")
    required_progress = {
        "CANONICAL_TYPED_FEED_ITEM_READS",
        "CANONICAL_EXPLICIT_SOURCE_BRIEF_BUILD",
        "CANONICAL_TYPED_SOURCE_BRIEF_READS",
        "MEMORY_AND_POSTGRES_LINEAGE_EVIDENCE",
        "API_020_TO_023_ADDITIVE_ISOLATION",
    }
    if not required_progress.issubset(set(f1.get("verified_progress", []))):
        fail("F1 verified Admin review progress is incomplete")
    if "ONE_CANONICAL_PUBLIC_FEED_MODEL" not in f1.get("exit_criteria", []):
        fail("F1 must explicitly require one canonical public-feed model")
    if "RESOLVE_PUBLIC_FEED_MODEL_CONFLICT" not in f1.get("remaining", []):
        fail("F1 must keep the public-feed conflict unresolved")

    canonical_lines = [
        line
        for line in registry.get("lines", [])
        if line.get("state") == "CANONICAL_INTEGRATION_TARGET"
    ]
    if len(canonical_lines) != 1:
        fail("registry must contain exactly one canonical integration target")
    if canonical_lines[0].get("sha") != CANONICAL_RUNTIME_SHA:
        fail("foundation program and registry canonical runtime differ")

    next_slice = program.get("next_runtime_slice", {})
    if next_slice.get("issue") != 291:
        fail("next runtime slice must reference Issue #291")
    if next_slice.get("primary_capability") != "CAP-055":
        fail("next runtime slice must primarily advance CAP-055")
    expected_caps = {
        "CAP-055",
        "CAP-056",
        "CAP-061",
        "CAP-065",
        "CAP-094",
        "CAP-095",
        "CAP-123",
        "CAP-126",
    }
    if set(next_slice.get("capabilities", [])) != expected_caps:
        fail("next public-feed convergence capability set drifted")
    if next_slice.get("base_sha") != CANONICAL_RUNTIME_SHA:
        fail("next runtime slice must start from the canonical runtime")
    if next_slice.get("resolves_conflict_group") != "PUBLIC_FEED_MODEL":
        fail("next runtime slice must resolve PUBLIC_FEED_MODEL")
    for guard in (
        "must_not_require_live_external_provider",
        "must_not_create_second_cms",
        "must_not_create_new_case_runtime_classes",
        "must_not_automatically_review_approve_or_publish",
        "must_preserve_zero_startup_activation",
    ):
        if next_slice.get(guard) is not True:
            fail(f"next runtime guard must remain enabled: {guard}")

    for cap_id in seen_caps:
        row = portfolio[cap_id]
        if (
            row["source"] == "conversation_proposal"
            and row["status"]
            not in FORBIDDEN_PROMOTED_STATUSES | {"ROADMAP_CANDIDATE"}
        ):
            fail(
                f"conversation proposal {cap_id} has unexpectedly promoted status "
                f"{row['status']}"
            )

    print(
        "foundation completion validation passed: "
        f"{len(waves)} waves, F0 complete, F1 in progress, "
        f"{len(seen_caps)} referenced capabilities"
    )


if __name__ == "__main__":
    main()

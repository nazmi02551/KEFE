#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/contracts/foundation-completion-program.v1.json"
PORTFOLIO = ROOT / "docs/roadmap/capability-portfolio.v1.tsv"

REQUIRED_WAVES = {f"F{index}" for index in range(8)}
FORBIDDEN_PROMOTED_STATUSES = {"PROPOSAL_REVIEW", "TEST", "VALIDATION_REQUIRED", "VALIDATION_ONLY"}


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
    portfolio = load_portfolio()

    waves = program.get("waves", [])
    wave_ids = [wave.get("id") for wave in waves]
    if set(wave_ids) != REQUIRED_WAVES or len(wave_ids) != len(REQUIRED_WAVES):
        fail(f"waves must be exactly {sorted(REQUIRED_WAVES)}")

    if not program["authority"].get("does_not_promote_working_to_current"):
        fail("WORKING/CURRENT authority boundary must remain explicit")
    if not program["authority"].get("does_not_promote_proposals_or_tests"):
        fail("proposal/test promotion guard must remain enabled")

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
        "CAP-055", "CAP-062", "CAP-063", "CAP-064", "CAP-065",
        "CAP-073", "CAP-084", "CAP-085", "CAP-095",
        "CAP-104", "CAP-114", "CAP-115", "CAP-116", "CAP-117", "CAP-124",
        "CAP-042", "CAP-043", "CAP-046", "CAP-047", "CAP-049", "CAP-054",
    }
    missing = sorted(mandatory - seen_caps)
    if missing:
        fail(f"mandatory foundation capabilities missing: {missing}")

    next_slice = program.get("next_runtime_slice", {})
    if next_slice.get("capability") != "CAP-062":
        fail("next runtime slice must remain CAP-062 until explicitly superseded")
    if not next_slice.get("must_not_create_second_cms"):
        fail("second-CMS guard must remain enabled")
    if not next_slice.get("must_not_require_external_provider_or_ai_calls"):
        fail("first projection runtime must remain provider/AI independent")
    if not next_slice.get("must_not_create_new_case_runtime_classes"):
        fail("generic runtime guard must remain enabled")

    for cap_id in seen_caps:
        row = portfolio[cap_id]
        if row["source"] == "conversation_proposal" and row["status"] not in FORBIDDEN_PROMOTED_STATUSES | {"ROADMAP_CANDIDATE"}:
            fail(f"conversation proposal {cap_id} has unexpectedly promoted status {row['status']}")

    print(
        "foundation completion validation passed: "
        f"{len(waves)} waves, {len(seen_caps)} referenced capabilities"
    )


if __name__ == "__main__":
    main()

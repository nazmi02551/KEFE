#!/usr/bin/env python3
"""Validate KEFE's canonical delivery-line convergence records.

The validator is deliberately network-free. It verifies repository-owned facts and
cross-file consistency; it does not claim that a recorded remote PR or workflow is
still open or green. Live GitHub state must still be read before merge.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path("docs/contracts/full-vision-delivery-convergence.v1.json")
REGISTRY_PATH = Path("docs/status/active-delivery-registry.v1.json")
CURRENT_PATH = Path("docs/status/CURRENT.md")
PORTFOLIO_PATH = Path("docs/roadmap/capability-portfolio.v1.tsv")
FOUNDATION_PATH = Path("docs/contracts/foundation-completion-program.v1.json")
AGENTS_PATH = Path("AGENTS.md")

SHA40 = re.compile(r"^[0-9a-f]{40}$")
CAP_ID = re.compile(r"^CAP-\d{3}$")
ZERO_SHA = "0" * 40


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing required file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object at {path}")
        return {}
    return value


def load_capabilities(errors: list[str]) -> set[str]:
    if not PORTFOLIO_PATH.is_file():
        errors.append(f"missing required file: {PORTFOLIO_PATH}")
        return set()
    try:
        with PORTFOLIO_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except OSError as exc:
        errors.append(f"cannot read {PORTFOLIO_PATH}: {exc}")
        return set()
    capabilities = {row.get("id", "") for row in rows}
    if len(rows) != 128:
        errors.append(f"portfolio must contain 128 rows, found {len(rows)}")
    invalid = sorted(value for value in capabilities if not CAP_ID.fullmatch(value))
    if invalid:
        errors.append(f"invalid portfolio capability IDs: {invalid}")
    return capabilities


def require_sha(value: Any, label: str, errors: list[str], *, allow_zero: bool = False) -> None:
    if not isinstance(value, str) or SHA40.fullmatch(value) is None:
        errors.append(f"{label} must be a lowercase 40-character SHA")
        return
    if value == ZERO_SHA and not allow_zero:
        errors.append(f"{label} must not be the zero SHA")


def main() -> int:
    errors: list[str] = []
    for path in (AGENTS_PATH, CURRENT_PATH, PORTFOLIO_PATH, FOUNDATION_PATH):
        if not path.is_file():
            errors.append(f"missing synchronized governance file: {path}")

    contract = load_json(CONTRACT_PATH, errors)
    registry = load_json(REGISTRY_PATH, errors)
    foundation = load_json(FOUNDATION_PATH, errors)
    known_capabilities = load_capabilities(errors)

    if contract.get("source_issue") != 287:
        errors.append("convergence contract must reference Issue #287")
    if contract.get("source_adr") != "docs/adr/0096-full-vision-delivery-convergence.md":
        errors.append("convergence contract must reference ADR-0096")
    authority = contract.get("authority")
    if not isinstance(authority, dict) or authority.get("delivery_registry") != str(REGISTRY_PATH):
        errors.append("convergence contract must bind the delivery registry path")

    allowed_states = set(contract.get("allowed_line_states") or [])
    required_states = {
        "CANONICAL_INTEGRATION_TARGET",
        "ACTIVE_REVIEW_RUNTIME",
        "CANDIDATE",
        "ALTERNATIVE",
        "SUPERSEDED",
        "EXTERNAL_GATE",
    }
    if allowed_states != required_states:
        errors.append(f"unexpected allowed line states: {sorted(allowed_states)}")

    contract_caps = contract.get("capabilities") or []
    if not isinstance(contract_caps, list) or not contract_caps:
        errors.append("convergence contract must list capabilities")
    else:
        unknown = sorted(set(contract_caps) - known_capabilities)
        if unknown:
            errors.append(f"contract references unknown capabilities: {unknown}")

    common = registry.get("common_divergence_base")
    if not isinstance(common, dict):
        errors.append("registry common_divergence_base must be an object")
        common_sha = None
    else:
        common_sha = common.get("sha")
        require_sha(common_sha, "registry.common_divergence_base.sha", errors)

    lines = registry.get("lines")
    if not isinstance(lines, list) or not lines:
        errors.append("registry must contain delivery lines")
        lines = []

    ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    canonical_lines: list[dict[str, Any]] = []
    capability_canonical_owners: dict[str, list[str]] = defaultdict(list)

    for index, raw_line in enumerate(lines):
        label = f"registry.lines[{index}]"
        if not isinstance(raw_line, dict):
            errors.append(f"{label} must be an object")
            continue
        line_id = raw_line.get("id")
        if not isinstance(line_id, str) or not line_id:
            errors.append(f"{label}.id must be non-empty")
            continue
        ids.append(line_id)
        by_id[line_id] = raw_line

        state = raw_line.get("state")
        if state not in allowed_states:
            errors.append(f"{line_id}: invalid state {state!r}")
        if state == "CANONICAL_INTEGRATION_TARGET":
            canonical_lines.append(raw_line)

        is_external = state == "EXTERNAL_GATE"
        require_sha(raw_line.get("sha"), f"{line_id}.sha", errors, allow_zero=is_external)
        require_sha(raw_line.get("common_base_sha"), f"{line_id}.common_base_sha", errors)
        if common_sha and raw_line.get("common_base_sha") != common_sha:
            errors.append(f"{line_id}: common base differs from registry common base")

        caps = raw_line.get("capability_boundaries")
        if not isinstance(caps, list) or not caps:
            errors.append(f"{line_id}: capability_boundaries must be non-empty")
            caps = []
        unknown = sorted(set(caps) - known_capabilities)
        if unknown:
            errors.append(f"{line_id}: unknown capability boundaries {unknown}")
        if state == "CANONICAL_INTEGRATION_TARGET":
            for cap in caps:
                capability_canonical_owners[cap].append(line_id)

        evidence = raw_line.get("evidence_state")
        if not isinstance(evidence, str) or not evidence:
            errors.append(f"{line_id}: evidence_state must be non-empty")
        if state in {"CANDIDATE", "ALTERNATIVE"} and "CANDIDATE" not in evidence and "ALTERNATIVE" not in evidence:
            errors.append(f"{line_id}: candidate/alternative evidence must remain explicitly bounded")

    duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate delivery line IDs: {duplicates}")
    if len(canonical_lines) != 1:
        errors.append(f"expected exactly one canonical integration target, found {len(canonical_lines)}")
    duplicate_canonical_caps = {
        cap: owners for cap, owners in capability_canonical_owners.items() if len(owners) > 1
    }
    if duplicate_canonical_caps:
        errors.append(f"capability boundaries have multiple canonical owners: {duplicate_canonical_caps}")

    conflict_groups = registry.get("conflict_groups")
    if not isinstance(conflict_groups, list):
        errors.append("registry conflict_groups must be a list")
        conflict_groups = []
    conflict_ids: set[str] = set()
    for index, raw_group in enumerate(conflict_groups):
        label = f"registry.conflict_groups[{index}]"
        if not isinstance(raw_group, dict):
            errors.append(f"{label} must be an object")
            continue
        group_id = raw_group.get("id")
        if not isinstance(group_id, str) or not group_id:
            errors.append(f"{label}.id must be non-empty")
            continue
        if group_id in conflict_ids:
            errors.append(f"duplicate conflict group: {group_id}")
        conflict_ids.add(group_id)
        members = raw_group.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{group_id}: conflict group needs at least two members")
            continue
        unknown_members = sorted(set(members) - set(by_id))
        if unknown_members:
            errors.append(f"{group_id}: unknown members {unknown_members}")
        if raw_group.get("resolution") == "PENDING_SEPARATE_ADR":
            canonical_members = [
                member for member in members
                if by_id.get(member, {}).get("state") == "CANONICAL_INTEGRATION_TARGET"
            ]
            if canonical_members:
                errors.append(f"{group_id}: unresolved conflict contains canonical members {canonical_members}")
        if raw_group.get("forbid_wholesale_merge") is not True:
            errors.append(f"{group_id}: unresolved overlap must forbid wholesale merge")

    next_integration = registry.get("next_integration")
    if not isinstance(next_integration, dict):
        errors.append("registry next_integration must be an object")
    else:
        base_line = next_integration.get("base_line")
        source_line = next_integration.get("source_line")
        if base_line not in by_id:
            errors.append(f"next integration references unknown base line {base_line!r}")
        elif by_id[base_line].get("state") != "CANONICAL_INTEGRATION_TARGET":
            errors.append("next integration base must be the canonical integration target")
        if source_line not in by_id:
            errors.append(f"next integration references unknown source line {source_line!r}")
        elif by_id[source_line].get("state") != "CANDIDATE":
            errors.append("next integration source must remain a candidate until exact integration evidence")
        blocked = set(next_integration.get("must_not_include_conflict_groups") or [])
        unknown_blocked = sorted(blocked - conflict_ids)
        if unknown_blocked:
            errors.append(f"next integration blocks unknown conflict groups {unknown_blocked}")

    foundation_waves = foundation.get("waves")
    if not isinstance(foundation_waves, list):
        errors.append("foundation program must contain waves")
    else:
        wave_ids = {wave.get("id") for wave in foundation_waves if isinstance(wave, dict)}
        if wave_ids != {f"F{index}" for index in range(8)}:
            errors.append(f"foundation waves must be exactly F0..F7, found {sorted(wave_ids)}")

    if CURRENT_PATH.is_file():
        current = CURRENT_PATH.read_text(encoding="utf-8")
        required_current_markers = [
            "active-delivery-registry.v1.json",
            "Registry version: `1.0.0`",
            "Issue #287",
            "ad825906388371eb9bb36b325abf36a2dd813c5c",
            "80fbc887f16651949ec36819c440154bcfc278a8",
            "00e1fd5ad8e4818d9a5738b6fdc9cd99bb3124fc",
            "e3c8a445ace3a9c4fbc734fa7ebf91e97b7c039e",
        ]
        for marker in required_current_markers:
            if marker not in current:
                errors.append(f"CURRENT.md missing convergence marker: {marker}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Full-vision delivery convergence PASS: "
        f"{len(lines)} lines, {len(conflict_groups)} conflict groups, "
        "one canonical integration target, zero errors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

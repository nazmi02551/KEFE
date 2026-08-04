#!/usr/bin/env python3
"""Validate KEFE's capability portfolio using only the Python standard library."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

PORTFOLIO = Path("docs/roadmap/capability-portfolio.v1.tsv")
CAP_ID = re.compile(r"^CAP-(\d{3})$")
PRIORITIES = {"P0", "P1", "P2", "P3"}
SOURCES = {"canonical", "conversation_proposal", "canonical_plus_conversation", "current_change"}
OWNER_IDS = {
    "KEFE-ADM-001", "KEFE-AED-001", "KEFE-AIA-001", "KEFE-CGD-001",
    "KEFE-CIV-001", "KEFE-CQB-001", "KEFE-CSL-001", "KEFE-DGS-001",
    "KEFE-DS-001", "KEFE-ENG-001", "KEFE-ETG-001", "KEFE-GOV-001",
    "KEFE-MPD-001", "KEFE-PB-001", "KEFE-RM-001", "KEFE-SEC-001",
    "KEFE-TIM-001",
}
REQUIRED = {
    "id", "slug", "title", "category", "status", "phase", "priority",
    "owners", "dependencies", "evidence", "source", "next_gate",
}
PROPOSAL_STATUSES = {
    "PROPOSAL_REVIEW", "TEST", "ROADMAP_CANDIDATE", "VALIDATION_ONLY",
    "VALIDATION_REQUIRED", "LONG_TERM",
}
IMPLEMENTED = {"IMPLEMENTED_VERIFIED", "IMPLEMENTED_THIS_CHANGE"}


def split(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def main() -> int:
    errors: list[str] = []
    with PORTFOLIO.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if set(reader.fieldnames or []) != REQUIRED:
            errors.append(f"invalid columns: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != 128:
        errors.append(f"expected 128 capabilities, found {len(rows)}")

    ids: list[str] = []
    slugs: list[str] = []
    for index, row in enumerate(rows, start=1):
        prefix = row.get("id") or f"row {index}"
        ids.append(row.get("id", ""))
        slugs.append(row.get("slug", ""))
        match = CAP_ID.fullmatch(row.get("id", ""))
        if match is None or int(match.group(1)) != index:
            errors.append(f"{prefix}: IDs must be contiguous CAP-001..CAP-128")
        if not row.get("slug") or row["slug"] != row["slug"].lower() or " " in row["slug"]:
            errors.append(f"{prefix}: invalid slug")
        if not row.get("title") or not row.get("category") or not row.get("phase"):
            errors.append(f"{prefix}: title/category/phase must be non-empty")
        if row.get("priority") not in PRIORITIES:
            errors.append(f"{prefix}: invalid priority {row.get('priority')!r}")
        if row.get("source") not in SOURCES:
            errors.append(f"{prefix}: invalid source {row.get('source')!r}")
        owners = split(row.get("owners", ""))
        if not owners:
            errors.append(f"{prefix}: at least one owner is required")
        unknown_owners = sorted(set(owners) - OWNER_IDS)
        if unknown_owners:
            errors.append(f"{prefix}: unknown owners {unknown_owners}")
        if row.get("status") in IMPLEMENTED and not split(row.get("evidence", "")):
            errors.append(f"{prefix}: implemented status requires evidence")
        if row.get("source") == "conversation_proposal" and row.get("status") not in PROPOSAL_STATUSES:
            errors.append(f"{prefix}: conversation proposal silently promoted to {row.get('status')}")

    for name, values in (("ID", ids), ("slug", slugs)):
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            errors.append(f"duplicate {name}s: {duplicates}")

    known = set(ids)
    for row in rows:
        unknown = sorted(set(split(row.get("dependencies", ""))) - known)
        if unknown:
            errors.append(f"{row['id']}: unknown dependencies {unknown}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    statuses = Counter(row["status"] for row in rows)
    print(f"Capability portfolio PASS: {len(rows)} capabilities, {len(statuses)} lifecycle states, zero errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

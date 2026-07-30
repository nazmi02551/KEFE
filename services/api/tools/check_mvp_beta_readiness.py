from __future__ import annotations

import re
from pathlib import Path

from kefe_api.infrastructure.beta_catalog import BETA_CATALOG, readiness_counts

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/mvp-completion-beta-gate.v1.yaml"
MOBILE_LIB = REPO_ROOT / "apps/mobile/lib"


def main() -> None:
    problems: list[str] = []
    counts = readiness_counts()
    if counts["DILEMMA"] < 20:
        problems.append(f"Beta catalog has only {counts['DILEMMA']} L0 DILEMMA cases")
    if counts["CALL"] < 4:
        problems.append(f"Beta catalog has only {counts['CALL']} L0 CALL cases")
    if any(item.base_format not in {"DILEMMA", "CALL"} for item in BETA_CATALOG):
        problems.append("Beta catalog contains unsupported MVP format")
    if any(not item.title.strip() or not item.prompt.strip() for item in BETA_CATALOG):
        problems.append("Beta catalog contains blank title/prompt")
    if len({item.case_id for item in BETA_CATALOG}) != len(BETA_CATALOG):
        problems.append("Beta catalog Case ids are not unique")
    if len({item.version_id for item in BETA_CATALOG}) != len(BETA_CATALOG):
        problems.append("Beta catalog CaseVersion ids are not unique")

    policy = CONTRACT.read_text(encoding="utf-8")
    required = {
        "minimum_l0_dilemma: 20",
        "minimum_l0_call: 4",
        "case_specific_runtime_classes: forbidden",
        "allowed_before_external_gates: MVP_CODE_COMPLETE_BETA_GATE_PENDING",
    }
    for fragment in sorted(required):
        if fragment not in policy:
            problems.append(f"MVP completion contract missing: {fragment}")

    # Runtime must stay Case-agnostic. Explicit fixture names/data are allowed in
    # infrastructure, but no format-specific Decision/Controller/Screen classes.
    forbidden_class = re.compile(r"class\s+\w*(?:Dilemma|Call)\w*(?:Screen|Controller|Service)")
    for path in MOBILE_LIB.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        if forbidden_class.search(text):
            problems.append(
                f"Case-specific mobile runtime class detected: {path.relative_to(REPO_ROOT)}"
            )

    if problems:
        raise SystemExit("\n".join(problems))
    print(
        "MVP beta readiness OK: "
        f"{counts['DILEMMA']} L0 DILEMMA + {counts['CALL']} L0 CALL; "
        "generic runtime boundary retained."
    )


if __name__ == "__main__":
    main()

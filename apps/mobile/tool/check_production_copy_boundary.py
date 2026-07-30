from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOBILE_LIB = ROOT / "apps" / "mobile" / "lib"
CONTRACT_PATH = ROOT / "docs" / "contracts" / "internal-alpha-hardening.v1.json"

STRING_LITERAL = re.compile(r"(?<![A-Za-z0-9_])(['\"])(.*?)(?<!\\)\1")
DIRECT_LOCALE_BRANCH = re.compile(
    r"languageCode\s*(?:==|!=)\s*['\"](?:tr|en)['\"]|\b(?:final|var|bool)\s+tr\s*="
)
TECHNICAL_LOWER_TOKEN = re.compile(r"^[a-z0-9_./${}-]+$")
TECHNICAL_UPPER_TOKEN = re.compile(r"^[A-Z0-9_.:-]+$")

ALLOWED_EXACT = {
    "KEFE",
    "DELETE",
    "tr",
    "en",
    "system",
    "light",
    "dark",
    "firstUse",
    "token",
    "caseId",
    "reason",
    "tags",
    "max_tags",
    "data_mode",
}


def scoped_files() -> list[Path]:
    result: list[Path] = []
    for path in MOBILE_LIB.rglob("*.dart"):
        rel = path.relative_to(MOBILE_LIB).as_posix()
        if rel.endswith("_strings.dart"):
            continue
        if rel in {"app/kefe_app.dart", "app/primary_navigation_shell.dart"}:
            result.append(path)
            continue
        if "/presentation/" in f"/{rel}":
            result.append(path)
    return sorted(result)


def is_technical_literal(value: str, line: str) -> bool:
    if value in ALLOWED_EXACT:
        return True
    if value.startswith(("/", "package:", "../", "../../")) or value.endswith(".dart"):
        return True
    if TECHNICAL_UPPER_TOKEN.fullmatch(value):
        return True
    if TECHNICAL_LOWER_TOKEN.fullmatch(value):
        # Lowercase tokens are implementation identifiers, stable keys or field names.
        return True
    if value.startswith("${") and re.sub(r"\$\{[^}]+\}", "", value).strip(" ·:%()/+-") == "":
        return True
    if "ValueKey" in line or "key:" in line:
        return True
    if "pathParameters" in line or "queryParameters" in line:
        return True
    return False


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["production_copy_boundary"]["required_violation_count"] == 0
    violations: list[str] = []

    for path in scoped_files():
        rel = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith(("import ", "export ", "part ")):
                continue
            if DIRECT_LOCALE_BRANCH.search(line):
                violations.append(f"{rel}:{line_no}: direct locale branching")
            for match in STRING_LITERAL.finditer(line):
                value = match.group(2)
                if not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", value):
                    continue
                if is_technical_literal(value, line):
                    continue
                violations.append(f"{rel}:{line_no}: user-facing literal {value!r}")

    if violations:
        print("Production localization boundary violations:")
        for violation in violations:
            print(f"- {violation}")
        print(f"Total: {len(violations)}")
        return 1

    print("Production localization boundary: PASS (0 violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

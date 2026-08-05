from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGETS = (
    ROOT / "services/api/tools/check_admin_operational_reports_contract.py",
    ROOT / "services/api/tools/export_admin_operational_reports_openapi_overlay.py",
)

for path in TARGETS:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    normalized = [line[4:] if line.startswith("    ") else line for line in lines]
    rendered = "\n".join(normalized).rstrip() + "\n"
    compile(rendered, str(path), "exec")
    path.write_text(rendered, encoding="utf-8")
    print(f"normalized generated Python indentation: {path.relative_to(ROOT)}")

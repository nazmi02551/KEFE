from __future__ import annotations

from pathlib import Path

path = Path(__file__).with_name("bootstrap_admin_operational_reports_surface.py")
content = path.read_text(encoding="utf-8")
start_marker = '''write(
    "services/api/tests/test_admin_operational_reports_http_postgres.py",
'''
end_marker = '''write(
    ".github/workflows/admin-operational-reports.yml",
'''
start = content.find(start_marker)
end = content.find(end_marker, start + len(start_marker))
if start < 0 or end < 0 or end <= start:
    raise SystemExit(f"unable to isolate PostgreSQL write block: start={start}, end={end}")
path.write_text(content[:start] + content[end:], encoding="utf-8")
print("PostgreSQL test write block removed from surface patcher")

from __future__ import annotations

from pathlib import Path

path = Path(__file__).with_name("bootstrap_admin_operational_reports_surface.py")
content = path.read_text(encoding="utf-8")
start = '''write(
    "services/api/tests/test_admin_operational_reports_http_postgres.py",
    """
'''
end = '''        finally:
            get_settings.cache_clear()
    """,
)

write(
    ".github/workflows/admin-operational-reports.yml",
'''
if content.count(start) != 1:
    raise SystemExit(f"unexpected PostgreSQL test opening count: {content.count(start)}")
if content.count(end) != 1:
    raise SystemExit(f"unexpected PostgreSQL test closing count: {content.count(end)}")
content = content.replace(
    start,
    '''write(
    "services/api/tests/test_admin_operational_reports_http_postgres.py",
    r\'''\'''
''',
    1,
)
content = content.replace(
    end,
    '''        finally:
            get_settings.cache_clear()
    \'''\''',
)

write(
    ".github/workflows/admin-operational-reports.yml",
''',
    1,
)
path.write_text(content, encoding="utf-8")
print("Operational Reports surface patcher quoting normalized")

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
API_SRC = REPO_ROOT / "services" / "api" / "src"
MIGRATIONS = REPO_ROOT / "services" / "api" / "migrations" / "versions"


def _contains_in_source(fragment: str) -> bool:
    return any(fragment in path.read_text(encoding="utf-8") for path in API_SRC.rglob("*.py"))


def main() -> None:
    problems: list[str] = []
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    policy = (CONTRACTS / "admin-session-persistence.v1.yaml").read_text(encoding="utf-8")
    schema = (CONTRACTS / "postgresql-m0-schema.v1.8.0.sql").read_text(encoding="utf-8")
    migration = (MIGRATIONS / "20260728_0010_admin_sessions.py").read_text(encoding="utf-8")

    manifest_fragments = {
        "manifest_version: 1.16.0",
        "path: docs/contracts/admin-session-persistence.v1.yaml",
        "path: docs/contracts/postgresql-m0-schema.v1.8.0.sql",
        "services/api/migrations/versions/20260728_0010_admin_sessions.py",
        "docs/adr/0016-durable-admin-sessions-and-csrf.md",
    }
    for fragment in sorted(manifest_fragments):
        if fragment not in manifest:
            problems.append(f"Admin session manifest missing: {fragment}")

    policy_fragments = {
        "schema: admin_security",
        "session_token_persisted_raw: false",
        "session_token_digest: sha256",
        "csrf_token_persisted_raw: false",
        "csrf_token_digest: sha256",
        "mfa_satisfied_at_required: true",
        "server_side_revocation: true",
        "bound_to_same_session: true",
        "login_endpoint_added_by_this_contract: false",
        "admin_authoring_endpoint_added_by_this_contract: false",
    }
    for fragment in sorted(policy_fragments):
        if fragment not in policy:
            problems.append(f"Admin session policy missing: {fragment}")

    schema_fragments = {
        "CREATE SCHEMA IF NOT EXISTS admin_security",
        "CREATE TABLE admin_security.subject",
        "CREATE TABLE admin_security.role_assignment",
        "CREATE TABLE admin_security.capability_grant",
        "CREATE TABLE admin_security.session",
        "CREATE TABLE admin_security.access_audit",
        "token_hash char(64) NOT NULL UNIQUE",
        "csrf_token_hash char(64) NOT NULL",
        "mfa_satisfied_at timestamptz NOT NULL",
        "revoked_at timestamptz",
        "admin_active_role_assignment_idx",
        "admin_active_capability_grant_idx",
    }
    for fragment in sorted(schema_fragments):
        if fragment not in schema:
            problems.append(f"Schema v1.8 missing Admin security invariant: {fragment}")

    migration_fragments = {
        'revision = "20260728_0010"',
        'down_revision = "20260728_0009"',
        "CREATE TABLE admin_security.session",
        "csrf_token_hash char(64) NOT NULL",
    }
    for fragment in sorted(migration_fragments):
        if fragment not in migration:
            problems.append(f"Admin session migration missing: {fragment}")

    source_fragments = {
        "class PostgresAdminSessionStore",
        "secrets.token_urlsafe(32)",
        "hashlib.sha256",
        "hmac.compare_digest",
        "def mark_seen(",
        "def record_step_up(",
        "def revoke(",
    }
    for fragment in sorted(source_fragments):
        if not _contains_in_source(fragment):
            problems.append(f"Admin session implementation missing: {fragment}")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Admin session contract OK: hashed opaque sessions, session-bound CSRF, MFA, "
        "revocation, roles/capabilities and no-HTTP-surface invariants verified."
    )


if __name__ == "__main__":
    main()

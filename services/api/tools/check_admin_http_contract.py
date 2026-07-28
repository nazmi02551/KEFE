from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "router.py"
)

EXPECTED_PATHS = {
    "/internal/admin/v1/session": {"get"},
    "/internal/admin/v1/cases": {"post"},
    "/internal/admin/v1/case-versions/{version_id}/revisions": {"post"},
    "/internal/admin/v1/case-versions/{version_id}": {"put"},
    "/internal/admin/v1/case-versions/{version_id}/submit": {"post"},
    "/internal/admin/v1/case-versions/{version_id}/approve": {"post"},
    "/internal/admin/v1/case-versions/{version_id}/reject": {"post"},
    "/internal/admin/v1/case-versions/{version_id}/publish": {"post"},
    "/internal/admin/v1/case-versions/{version_id}/withdraw": {"post"},
    "/internal/admin/v1/cases/{case_id}/audit": {"get"},
}

WRITE_METHODS = {"post", "put", "patch", "delete"}
FORBIDDEN_IDENTITY_FIELDS = {"actor_ref", "admin_subject_id", "roles", "capabilities"}
FORBIDDEN_SECRET_FIELDS = {"session_token", "csrf_token"}


def _request_schema_name(operation: dict) -> str | None:
    schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        return ref.rsplit("/", 1)[-1]
    return None


def main() -> None:
    policy = (CONTRACTS / "admin-http-surface.v1.yaml").read_text(encoding="utf-8")
    router_source = ROUTER.read_text(encoding="utf-8")
    openapi = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))
    schemas = openapi.get("components", {}).get("schemas", {})
    paths = openapi.get("paths", {})

    problems: list[str] = []

    required_policy = {
        "route_prefix: /internal/admin/v1",
        "name: kefe_admin_session",
        "header: X-KEFE-CSRF",
        "bound_to_same_session: true",
        "verify_before_mutation: true",
        "consumer_credentials_accepted: false",
        "admin_login_endpoint_in_scope: false",
        "facade: SecuredContentAuthoringService",
        "direct_repository_mutation_from_http: forbidden",
        "audit_actor_ref: server_derived",
    }
    for fragment in sorted(required_policy):
        if fragment not in policy:
            problems.append(f"Admin HTTP contract missing: {fragment}")

    required_source = {
        'ADMIN_SESSION_COOKIE = "kefe_admin_session"',
        'ADMIN_CSRF_HEADER = "X-KEFE-CSRF"',
        'prefix="/internal/admin/v1"',
        "SecuredContentAuthoringService",
        "security.resolve_session(session_token)",
        "security.touch(principal)",
        "get_csrf_verifier(request).verify(",
    }
    for fragment in sorted(required_source):
        if fragment not in router_source:
            problems.append(f"Admin HTTP router missing: {fragment}")

    if "/internal/admin/v1/login" in paths:
        problems.append("Admin HTTP surface must not expose a login/SSO endpoint yet")

    for path, methods in EXPECTED_PATHS.items():
        item = paths.get(path)
        if item is None:
            problems.append(f"OpenAPI missing Admin path: {path}")
            continue
        for method in methods:
            operation = item.get(method)
            if operation is None:
                problems.append(f"OpenAPI missing Admin operation: {method.upper()} {path}")
                continue
            if method in WRITE_METHODS:
                parameters = operation.get("parameters", [])
                csrf = [
                    parameter
                    for parameter in parameters
                    if parameter.get("in") == "header"
                    and parameter.get("name", "").lower() == "x-kefe-csrf"
                ]
                if not csrf:
                    problems.append(f"Admin write missing CSRF header contract: {method.upper()} {path}")

            schema_name = _request_schema_name(operation)
            if schema_name:
                properties = schemas.get(schema_name, {}).get("properties", {})
                leaked = sorted(FORBIDDEN_IDENTITY_FIELDS & properties.keys())
                if leaked:
                    problems.append(
                        f"{schema_name} accepts forbidden Admin identity fields: {', '.join(leaked)}"
                    )

    for schema_name, schema in schemas.items():
        if not schema_name.startswith("Admin") and schema_name not in {
            "AuthoringVersionResponse",
            "AuditTrailResponse",
        }:
            continue
        properties = schema.get("properties", {})
        leaked = sorted(FORBIDDEN_SECRET_FIELDS & properties.keys())
        if leaked:
            problems.append(
                f"{schema_name} exposes forbidden Admin secrets: {', '.join(leaked)}"
            )

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Admin HTTP contract OK: internal route set, same-session CSRF, "
        "server-derived identity and secret non-disclosure verified."
    )


if __name__ == "__main__":
    main()

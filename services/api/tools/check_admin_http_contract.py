from __future__ import annotations

from pathlib import Path

from export_openapi import load_expected_contract

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
SOURCE_SUBSCRIPTION_ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "source_subscription_router.py"
)
CONFIG_ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "content_configuration"
    / "admin_router.py"
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
    "/internal/admin/v1/content-configuration/current": {"get"},
    "/internal/admin/v1/content-configuration/versions": {"get"},
    "/internal/admin/v1/content-configuration/versions/{version_id}": {"get", "put"},
    "/internal/admin/v1/content-configuration/audit": {"get"},
    "/internal/admin/v1/content-configuration/drafts": {"post"},
    "/internal/admin/v1/content-configuration/versions/{version_id}/publish": {"post"},
    "/internal/admin/v1/content-configuration/versions/{version_id}/rollback-drafts": {
        "post"
    },
    "/internal/admin/v1/source-subscriptions": {"get"},
    "/internal/admin/v1/source-subscriptions/{subscription_code}/activate": {
        "post"
    },
}
WRITE_METHODS = {"post", "put", "patch", "delete"}
COMMON_FORBIDDEN_IDENTITY_FIELDS = {
    "actor_ref",
    "admin_subject_id",
    "roles",
    "audit_identity",
    "created_by",
}
AUTHORING_FORBIDDEN_IDENTITY_FIELDS = COMMON_FORBIDDEN_IDENTITY_FIELDS | {
    "capabilities"
}
CONFIGURATION_FORBIDDEN_METADATA_FIELDS = COMMON_FORBIDDEN_IDENTITY_FIELDS | {
    "capabilities_grant",
    "version_no",
    "state",
    "lifecycle_state",
    "created_at",
    "published_at",
    "cloned_from_version_id",
}
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
    config_policy = (CONTRACTS / "admin-content-configuration-http.v1.yaml").read_text(
        encoding="utf-8"
    )
    router_source = ROUTER.read_text(encoding="utf-8")
    source_subscription_router = SOURCE_SUBSCRIPTION_ROUTER.read_text(
        encoding="utf-8"
    )
    config_router_source = CONFIG_ROUTER.read_text(encoding="utf-8")
    openapi = load_expected_contract(CONTRACTS / "openapi.v1.json")
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

    required_config_policy = {
        "route_prefix: /internal/admin/v1/content-configuration",
        "application_service: SecuredContentConfigurationService",
        "direct_repository_mutation_from_http: forbidden",
        "consumer_credentials_accepted: false",
        "csrf_bound_to_same_session: true",
        "manage: TAXONOMY_MANAGE",
        "audit_read: AUDIT_READ",
        "audit_actor_ref: server_derived",
    }
    for fragment in sorted(required_config_policy):
        if fragment not in config_policy:
            problems.append(f"Admin configuration HTTP contract missing: {fragment}")

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

    required_source_subscription_source = {
        'prefix="/internal/admin/v1/source-subscriptions"',
        "SecuredRssAtomSubscriptionService",
        "principal: ReadPrincipalDep",
        "principal: WritePrincipalDep",
        '"/{subscription_code}/activate"',
        'pattern=r"^sha256:[0-9a-f]{64}$"',
    }
    for fragment in sorted(required_source_subscription_source):
        if fragment not in source_subscription_router:
            problems.append(f"Admin source subscription router missing: {fragment}")
    for forbidden in ("@router.put", "@router.delete", '@router.post(""'):
        if forbidden in source_subscription_router:
            problems.append(
                f"Admin source subscription router exposes mutation route: {forbidden}"
            )

    required_config_source = {
        'prefix="/internal/admin/v1/content-configuration"',
        "SecuredContentConfigurationService",
        "configuration.create_draft_from_current(principal)",
        "configuration.draft_for_edit(principal, version_id)",
        "configuration.publish(principal, version_id)",
        "configuration.audit_trail(principal)",
    }
    for fragment in sorted(required_config_source):
        if fragment not in config_router_source:
            problems.append(f"Admin configuration router missing: {fragment}")
    if "ContentConfigurationRepository" in config_router_source:
        problems.append("Admin configuration HTTP must not depend directly on repository")

    if "/internal/admin/v1/login" in paths:
        problems.append("Admin HTTP surface must not expose a login/SSO endpoint yet")

    for path, methods in EXPECTED_PATHS.items():
        item = paths.get(path)
        if item is None:
            problems.append(f"OpenAPI missing Admin path: {path}")
            continue
        unexpected_methods = set(item) - methods
        if unexpected_methods:
            problems.append(
                f"OpenAPI exposes unexpected Admin methods at {path}: "
                + ", ".join(sorted(unexpected_methods))
            )
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
                    problems.append(
                        "Admin write missing CSRF header contract: "
                        f"{method.upper()} {path}"
                    )

            schema_name = _request_schema_name(operation)
            if schema_name:
                properties = schemas.get(schema_name, {}).get("properties", {})
                forbidden_fields = (
                    CONFIGURATION_FORBIDDEN_METADATA_FIELDS
                    if path.startswith("/internal/admin/v1/content-configuration")
                    else AUTHORING_FORBIDDEN_IDENTITY_FIELDS
                )
                leaked = sorted(forbidden_fields & properties.keys())
                if leaked:
                    problems.append(
                        f"{schema_name} accepts forbidden Admin identity/metadata fields: "
                        + ", ".join(leaked)
                    )

    for schema_name, schema in schemas.items():
        if not (
            schema_name.startswith("Admin")
            or schema_name.startswith("Configuration")
            or schema_name.startswith("SourceSubscription")
            or schema_name in {
                "ActivateSourceSubscriptionRequest",
                "AuthoringVersionResponse",
                "AuditTrailResponse",
            }
        ):
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
        "Admin HTTP contract OK: authoring, composable configuration and guarded "
        "source subscriptions; same-session CSRF, server-derived identity and "
        "secret non-disclosure verified."
    )


if __name__ == "__main__":
    main()

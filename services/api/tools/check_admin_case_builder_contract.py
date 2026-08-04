from __future__ import annotations

import json
from pathlib import Path

from export_openapi import build_openapi

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "admin-case-builder-draft-workspace.v1.json"
ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "case_builder_router.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"

READ_PATH = "/internal/admin/v1/case-builder/case-versions/{version_id}"
SUBMIT_PATH = "/internal/admin/v1/case-versions/{version_id}/submit"
AUDIT_PATH = "/internal/admin/v1/cases/{case_id}/audit"
FORBIDDEN_INPUT_FIELDS = {
    "completed_review_modes",
    "flow_template_code",
    "flow_template_version_no",
    "content_configuration_id",
    "content_configuration_version_no",
    "resolved_flow",
    "state",
    "published_at",
    "actor_ref",
}
FORBIDDEN_RESPONSE_FIELDS = {
    "raw_evidence_body",
    "credential",
    "secret",
    "provider_secret_ref",
    "storage_ref",
    "backend_object_key",
    "session_token",
    "csrf_token",
}
REQUIRED_RESPONSE_FIELDS = {
    "id",
    "case_id",
    "version_no",
    "state",
    "title",
    "summary",
    "base_format_code",
    "primary_domain_code",
    "content_risk",
    "issues",
    "context_blocks",
    "sources",
    "modifiers",
    "is_fact_bearing",
    "is_real_event",
    "required_review_modes",
    "completed_review_modes",
    "flow_template_code",
    "flow_template_version_no",
    "content_locale",
    "market_scope",
    "country_codes",
    "cultural_context_note",
    "legal_context_note",
    "localizations",
    "created_at",
    "published_at",
}


def _schema(openapi: dict[str, object], name: str) -> dict[str, object]:
    schemas = openapi.get("components", {}).get("schemas", {})
    value = schemas.get(name)
    if not isinstance(value, dict):
        raise SystemExit(f"OpenAPI schema missing: {name}")
    return value


def _request_schema_name(operation: dict[str, object]) -> str:
    schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        raise SystemExit("Case Builder PUT must use one strict JSON request schema")
    return ref.rsplit("/", 1)[-1]


def _response_schema_name(operation: dict[str, object], status: str) -> str:
    schema = (
        operation.get("responses", {})
        .get(status, {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        raise SystemExit(f"Case Builder response {status} must use one strict schema")
    return ref.rsplit("/", 1)[-1]


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    openapi = build_openapi()
    paths = openapi.get("paths", {})
    problems: list[str] = []

    if contract.get("version") != "1.0.1":
        problems.append("Case Builder executable contract version must be 1.0.1")
    if contract.get("parent_runtime_sha") != "59f70896c8d9df91727c158da936630bd6bddd6c":
        problems.append("Case Builder parent runtime SHA drifted")

    required_source = {
        'prefix="/internal/admin/v1/case-builder"',
        "ReadPrincipalDep",
        "WritePrincipalDep",
        "AuthoringDep",
        "authoring.draft_for_edit(principal, version_id)",
        "authoring.save_draft(principal, updated)",
        "CaseBuilderDraftInput",
        "CaseBuilderVersionResponse",
    }
    for fragment in sorted(required_source):
        if fragment not in source:
            problems.append(f"Case Builder router missing: {fragment}")

    for forbidden in (
        "ContentAuthoringRepository",
        ".approve(",
        ".reject(",
        ".publish(",
        ".withdraw(",
        "raw_evidence_body",
        "provider_secret_ref",
        "backend_object_key",
    ):
        if forbidden in source:
            problems.append(f"Case Builder router contains forbidden authority/data: {forbidden}")

    if "app.include_router(admin_case_builder_router)" not in main_source:
        problems.append("Case Builder router is not composed into the canonical app")

    item = paths.get(READ_PATH)
    if not isinstance(item, dict):
        problems.append(f"OpenAPI missing Case Builder path: {READ_PATH}")
    else:
        if "get" not in item or "put" not in item:
            problems.append("Case Builder path must expose exactly GET and PUT operations")
        unexpected = sorted(set(item) - {"get", "put", "parameters"})
        if unexpected:
            problems.append(f"Case Builder path has unexpected operations: {unexpected}")

        put = item.get("put")
        if isinstance(put, dict):
            csrf = [
                parameter
                for parameter in put.get("parameters", [])
                if parameter.get("in") == "header"
                and parameter.get("name", "").lower() == "x-kefe-csrf"
            ]
            if not csrf:
                problems.append("Case Builder PUT is missing same-session CSRF header")
            request_schema_name = _request_schema_name(put)
            request_properties = set(_schema(openapi, request_schema_name).get("properties", {}))
            leaked = sorted(FORBIDDEN_INPUT_FIELDS & request_properties)
            if leaked:
                problems.append(
                    "Case Builder request accepts server/Flow-owned fields: " + ", ".join(leaked)
                )
            response_schema_name = _response_schema_name(put, "200")
            response_properties = set(_schema(openapi, response_schema_name).get("properties", {}))
            missing = sorted(REQUIRED_RESPONSE_FIELDS - response_properties)
            leaked_response = sorted(FORBIDDEN_RESPONSE_FIELDS & response_properties)
            if missing:
                problems.append(
                    "Case Builder response missing round-trip fields: " + ", ".join(missing)
                )
            if leaked_response:
                problems.append(
                    "Case Builder response leaks forbidden fields: " + ", ".join(leaked_response)
                )

    for required_path, method in ((SUBMIT_PATH, "post"), (AUDIT_PATH, "get")):
        if method not in paths.get(required_path, {}):
            problems.append(
                f"Required existing lifecycle operation missing: {method.upper()} {required_path}"
            )

    for command in ("approve", "reject", "publish", "withdraw"):
        forbidden_path = f"{READ_PATH}/{command}"
        if forbidden_path in paths:
            problems.append(f"Case Builder must not expose lifecycle command: {command}")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Admin Case Builder contract: PASS — additive adapter delegates to the single "
        "Content Authoring aggregate, preserves Flow/review authority and exposes only "
        "explicit DRAFT save plus the existing separate submit/audit operations."
    )


if __name__ == "__main__":
    main()

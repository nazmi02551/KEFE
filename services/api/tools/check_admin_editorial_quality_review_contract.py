from __future__ import annotations

import json
from pathlib import Path

from export_openapi import build_openapi

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "admin-editorial-quality-review-workspace.v1.json"
)
ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "editorial_quality_review_router.py"
)
SECURED = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "content_authoring.py"
)
PORTS = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "content_authoring"
    / "ports.py"
)
MEMORY = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "content_authoring"
    / "in_memory.py"
)
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_flow_pinned_content_authoring.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"

QUEUE_PATH = "/internal/admin/v1/content-reviews"
DETAIL_PATH = "/internal/admin/v1/content-reviews/{version_id}"
DECISION_PATH = "/internal/admin/v1/content-reviews/{version_id}/decision"
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


def _schema(openapi: dict[str, object], name: str) -> dict[str, object]:
    schemas = openapi.get("components", {}).get("schemas", {})
    value = schemas.get(name)
    if not isinstance(value, dict):
        raise SystemExit(f"OpenAPI schema missing: {name}")
    return value


def _ref_name(operation: dict[str, object], *, request: bool) -> str:
    if request:
        schema = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
    else:
        schema = (
            operation.get("responses", {})
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        kind = "request" if request else "response"
        raise SystemExit(f"Editorial quality review {kind} must use one strict schema")
    return ref.rsplit("/", 1)[-1]


def _collect_property_names(value: object) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for item in value.values():
            names.update(_collect_property_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_property_names(item))
    return names


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    router = ROUTER.read_text(encoding="utf-8")
    secured = SECURED.read_text(encoding="utf-8")
    ports = PORTS.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    openapi = build_openapi()
    paths = openapi.get("paths", {})
    problems: list[str] = []

    if contract.get("version") != "1.0.0":
        problems.append("Editorial quality review contract version must remain 1.0.0")
    parent = contract.get("parent_runtime", {})
    if parent.get("pr") != 299 or parent.get("sha") != (
        "612c57fa2188c7f9c5fae8f64fcfebbca644cfbc"
    ):
        problems.append("Editorial quality review exact parent drifted")

    for fragment in (
        'prefix="/internal/admin/v1/content-reviews"',
        "ReadPrincipalDep",
        "WritePrincipalDep",
        "authoring.review_queue(",
        "authoring.review_for_inspection(",
        "authoring.approve_with_review_modes(",
        "authoring.reject(",
        'Literal["APPROVE", "REJECT"]',
        "next_offset",
    ):
        if fragment not in router:
            problems.append(f"Editorial review router missing: {fragment}")

    for fragment in (
        "AdminCapability.CONTENT_REVIEW",
        "enforce_reviewer_separation",
        "explicit_attestation",
        "CONTENT_REVIEW_ATTESTATION_REQUIRED",
        "CONTENT_REVIEW_MODES_INCOMPLETE",
        "completed_review_modes=()",
        "expected_state=ContentLifecycle.IN_REVIEW",
    ):
        if fragment not in secured:
            problems.append(f"Secured review service missing: {fragment}")

    for source_name, source in (
        ("ports", ports),
        ("memory", memory),
        ("postgres", postgres),
    ):
        if "def list_by_state(" not in source:
            problems.append(f"{source_name} authoring adapter lacks bounded state query")

    for fragment in (
        "ORDER BY created_at DESC, id DESC",
        "LIMIT :limit OFFSET :offset",
        "lifecycle_state = :state",
    ):
        if fragment not in postgres:
            problems.append(f"PostgreSQL review query missing: {fragment}")

    if "app.include_router(admin_editorial_quality_review_router)" not in main_source:
        problems.append("Editorial quality review router is not composed into canonical app")

    queue_item = paths.get(QUEUE_PATH)
    if not isinstance(queue_item, dict) or set(queue_item) - {"get", "parameters"}:
        problems.append("Review queue must expose GET only")
    detail_item = paths.get(DETAIL_PATH)
    if not isinstance(detail_item, dict) or set(detail_item) - {"get", "parameters"}:
        problems.append("Review detail must expose GET only")
    decision_item = paths.get(DECISION_PATH)
    if not isinstance(decision_item, dict) or set(decision_item) - {"post", "parameters"}:
        problems.append("Review decision must expose POST only")
    elif isinstance(decision_item.get("post"), dict):
        operation = decision_item["post"]
        csrf = [
            parameter
            for parameter in operation.get("parameters", [])
            if parameter.get("in") == "header"
            and parameter.get("name", "").lower() == "x-kefe-csrf"
        ]
        if not csrf:
            problems.append("Review decision is missing same-session CSRF header")
        request_schema = _schema(openapi, _ref_name(operation, request=True))
        request_properties = set(request_schema.get("properties", {}))
        if request_properties != {"decision", "completed_review_modes", "rationale"}:
            problems.append(
                "Review decision request field set drifted: "
                + ", ".join(sorted(request_properties))
            )
        response_schema = _schema(openapi, _ref_name(operation, request=False))
        leaked = sorted(
            FORBIDDEN_RESPONSE_FIELDS & _collect_property_names(response_schema)
        )
        if leaked:
            problems.append("Review response leaks forbidden fields: " + ", ".join(leaked))

    for forbidden in (
        "/publish",
        "/withdraw",
        "/edit",
        "raw_evidence_body",
        "provider_secret_ref",
        "backend_object_key",
    ):
        if forbidden in router:
            problems.append(
                "Editorial review router contains forbidden authority/data: "
                f"{forbidden}"
            )

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Admin Editorial Quality Review contract: PASS — bounded IN_REVIEW queue, "
        "reviewer-only inspection, exact review-mode attestation, maker-checker approval, "
        "rationale-bound rejection and no publication/Flow authority are enforced."
    )


if __name__ == "__main__":
    main()

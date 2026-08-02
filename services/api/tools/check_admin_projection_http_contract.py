from __future__ import annotations

from pathlib import Path

from export_openapi import load_expected_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "admin-editorial-projection-http-slice34.v1.json"
)
POLICY = REPO_ROOT / "docs" / "contracts" / "admin-http-surface.v1.yaml"
OPENAPI = REPO_ROOT / "docs" / "contracts" / "openapi.v1.json"
ROUTER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "editorial_projection_router.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
PATH = "/internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection"
FORBIDDEN_REQUEST_FIELDS = {
    "actor_ref",
    "requested_by_admin_ref",
    "admin_subject_id",
    "roles",
    "capabilities",
    "state",
    "lifecycle_state",
    "authoring_case_id",
    "authoring_case_version_id",
}


def main() -> int:
    required = (CONTRACT, POLICY, OPENAPI, ROUTER, MAIN)
    problems = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in required
        if not path.exists()
    ]
    if problems:
        print("\n".join(problems))
        return 1

    contract = CONTRACT.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    app = MAIN.read_text(encoding="utf-8")
    openapi = load_expected_contract(OPENAPI)

    required_contract = (
        '"application_service": "SecuredEditorialProjectionService"',
        '"capability": "CONTENT_PROJECT"',
        '"csrf_required": true',
        '"request_supplied_actor_forbidden": true',
        '"same_input_same_idempotency_returns_replay": true',
        '"creates_draft_only": true',
    )
    for fragment in required_contract:
        if fragment not in contract:
            problems.append(f"Slice 34 contract missing: {fragment}")

    required_policy = (
        "projection_facade: SecuredEditorialProjectionService",
        "path: /candidate-proposals/{candidate_proposal_id}/projection",
        "capability: CONTENT_PROJECT",
        "actor_identity: server_derived",
        "creates_lifecycle_state: DRAFT",
    )
    for fragment in required_policy:
        if fragment not in policy:
            problems.append(f"Admin HTTP policy missing: {fragment}")

    required_router = (
        'prefix="/internal/admin/v1"',
        '"/candidate-proposals/{candidate_proposal_id}/projection"',
        "class EditorialProjectionRequest(StrictModel):",
        "class EditorialProjectionResponse(StrictModel):",
        "principal: WritePrincipalDep",
        "SecuredEditorialProjectionService",
        "projection.project(",
        'lifecycle_state="DRAFT"',
        "replayed=result.replayed",
    )
    for fragment in required_router:
        if fragment not in router:
            problems.append(f"Projection router missing: {fragment}")
    for forbidden in (
        "EditorialProjectionRepository",
        "IngestionOrchestrationRepository",
        "requested_by_admin_ref=body",
        "actor_ref=body",
        ".publish(",
        ".approve(",
        ".submit_for_review(",
    ):
        if forbidden in router:
            problems.append(f"Projection router contains forbidden boundary: {forbidden}")

    if "app.include_router(admin_editorial_projection_router)" not in app:
        problems.append("Application does not include Admin Editorial Projection router")

    operation = openapi.get("paths", {}).get(PATH, {}).get("post")
    if operation is None:
        problems.append(f"OpenAPI missing POST {PATH}")
    else:
        parameters = operation.get("parameters", [])
        if not any(
            item.get("in") == "header"
            and item.get("name", "").lower() == "x-kefe-csrf"
            for item in parameters
        ):
            problems.append("Projection HTTP operation is missing X-KEFE-CSRF header")
        request_schema = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
            .get("$ref", "")
            .rsplit("/", 1)[-1]
        )
        schemas = openapi.get("components", {}).get("schemas", {})
        properties = schemas.get(request_schema, {}).get("properties", {})
        leaked = sorted(FORBIDDEN_REQUEST_FIELDS & properties.keys())
        if leaked:
            problems.append(
                "Projection request accepts forbidden identity/lifecycle fields: "
                + ", ".join(leaked)
            )
        response_ref = (
            operation.get("responses", {})
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
            .get("$ref", "")
            .rsplit("/", 1)[-1]
        )
        response_properties = schemas.get(response_ref, {}).get("properties", {})
        for field in ("lifecycle_state", "replayed", "projection_record_id"):
            if field not in response_properties:
                problems.append(f"Projection response missing field: {field}")

    if problems:
        print("Admin Editorial Projection HTTP contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Admin Editorial Projection HTTP contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

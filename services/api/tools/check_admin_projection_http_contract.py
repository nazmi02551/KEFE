from __future__ import annotations

import json
from pathlib import Path

from export_openapi import load_expected_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "admin-editorial-operations-slice34.v1.json"
)
POLICY = REPO_ROOT / "docs" / "contracts" / "admin-http-surface.v1.yaml"
OPENAPI = REPO_ROOT / "docs" / "contracts" / "openapi.v1.json"
ADMIN_DIR = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
)
ROUTER = ADMIN_DIR / "editorial_projection_router.py"
REVIEW_SERVICE = ADMIN_DIR / "proposal_review.py"
PROJECTION_SERVICE = ADMIN_DIR / "editorial_projection.py"
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
REVIEW_PATH = "/internal/admin/v1/proposals/{proposal_id}/review"
PROJECTION_PATH = (
    "/internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection"
)
FORBIDDEN_REQUEST_FIELDS = {
    "actor_ref",
    "reviewer_ref",
    "requested_by_admin_ref",
    "admin_subject_id",
    "roles",
    "capabilities",
    "state",
    "lifecycle_state",
    "authoring_case_id",
    "authoring_case_version_id",
}


def _operation(openapi: dict[str, object], path: str) -> dict[str, object] | None:
    return openapi.get("paths", {}).get(path, {}).get("post")


def _schema_properties(
    openapi: dict[str, object],
    operation: dict[str, object],
) -> dict[str, object]:
    ref = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
        .rsplit("/", 1)[-1]
    )
    return openapi.get("components", {}).get("schemas", {}).get(ref, {}).get(
        "properties",
        {},
    )


def _has_csrf(operation: dict[str, object]) -> bool:
    return any(
        item.get("in") == "header"
        and item.get("name", "").lower() == "x-kefe-csrf"
        for item in operation.get("parameters", [])
    )


def main() -> int:
    required = (
        CONTRACT,
        POLICY,
        OPENAPI,
        ROUTER,
        REVIEW_SERVICE,
        PROJECTION_SERVICE,
        MAIN,
    )
    problems = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in required
        if not path.exists()
    ]
    if problems:
        print("\n".join(problems))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    policy = POLICY.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    review_service = REVIEW_SERVICE.read_text(encoding="utf-8")
    projection_service = PROJECTION_SERVICE.read_text(encoding="utf-8")
    app = MAIN.read_text(encoding="utf-8")
    openapi = load_expected_contract(OPENAPI)

    if contract.get("capabilities") != [
        "CAP-061",
        "CAP-062",
        "CAP-063",
        "CAP-065",
    ]:
        problems.append("Slice 34 capability set/order is not locked")
    if contract.get("proposal_review", {}).get("automatic_projection") is not False:
        problems.append("Proposal review must explicitly forbid automatic projection")
    projection = contract.get("editorial_projection", {})
    for field in (
        "automatic_submit",
        "automatic_authoring_review",
        "automatic_approval",
        "automatic_publication",
        "consumer_materialization",
    ):
        if projection.get(field) is not False:
            problems.append(f"Projection contract must keep {field}=false")
    if projection.get("creates_lifecycle_state") != "DRAFT":
        problems.append("Projection contract must create DRAFT only")

    required_policy = (
        "proposal_review_facade: SecuredProposalReviewService",
        "projection_facade: SecuredEditorialProjectionService",
        "path: /proposals/{proposal_id}/review",
        "capability: CONTENT_REVIEW",
        "automatic_projection: forbidden",
        "path: /candidate-proposals/{candidate_proposal_id}/projection",
        "capability: CONTENT_PROJECT",
        "creates_lifecycle_state: DRAFT",
    )
    for fragment in required_policy:
        if fragment not in policy:
            problems.append(f"Admin HTTP policy missing: {fragment}")

    required_router = (
        'prefix="/internal/admin/v1"',
        '"/proposals/{proposal_id}/review"',
        '"/candidate-proposals/{candidate_proposal_id}/projection"',
        "class ProposalReviewRequest(StrictModel):",
        "class EditorialProjectionRequest(StrictModel):",
        "principal: WritePrincipalDep",
        "review.review(",
        "projection.project(",
        'lifecycle_state="DRAFT"',
    )
    for fragment in required_router:
        if fragment not in router:
            problems.append(f"Admin editorial router missing: {fragment}")
    for forbidden in (
        "EditorialProjectionRepository",
        "IngestionOrchestrationRepository",
        "requested_by_admin_ref=body",
        "reviewer_ref=body",
        "actor_ref=body",
        ".publish(",
        ".approve(",
        ".submit_for_review(",
    ):
        if forbidden in router:
            problems.append(f"Admin editorial router contains forbidden boundary: {forbidden}")

    for fragment in (
        "AdminCapability.CONTENT_REVIEW",
        "reviewer_ref=principal.audit_actor_ref",
        "INGESTION_PROPOSAL_NOT_FOUND",
        "INGESTION_PROPOSAL_ALREADY_REVIEWED",
    ):
        if fragment not in review_service:
            problems.append(f"Proposal review service missing: {fragment}")
    for forbidden in (
        "EditorialProjectionService",
        "SecuredEditorialProjectionService",
        ".project(",
        ".publish(",
    ):
        if forbidden in review_service:
            problems.append(f"Proposal review service may not contain: {forbidden}")

    for fragment in (
        "AdminCapability.CONTENT_PROJECT",
        "requested_by_admin_ref=principal.audit_actor_ref",
        "EditorialProjectionCommand(",
    ):
        if fragment not in projection_service:
            problems.append(f"Projection service missing: {fragment}")

    if "app.include_router(admin_editorial_projection_router)" not in app:
        problems.append("Application does not include Admin editorial operations router")

    for path in (REVIEW_PATH, PROJECTION_PATH):
        operation = _operation(openapi, path)
        if operation is None:
            problems.append(f"OpenAPI missing POST {path}")
            continue
        if not _has_csrf(operation):
            problems.append(f"POST {path} is missing X-KEFE-CSRF header")
        leaked = sorted(FORBIDDEN_REQUEST_FIELDS & _schema_properties(openapi, operation))
        if leaked:
            problems.append(
                f"POST {path} accepts forbidden identity/lifecycle fields: "
                + ", ".join(leaked)
            )

    projection_operation = _operation(openapi, PROJECTION_PATH)
    if projection_operation is not None:
        response_ref = (
            projection_operation.get("responses", {})
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
            .get("$ref", "")
            .rsplit("/", 1)[-1]
        )
        response_properties = (
            openapi.get("components", {})
            .get("schemas", {})
            .get(response_ref, {})
            .get("properties", {})
        )
        for field in ("lifecycle_state", "replayed", "projection_record_id"):
            if field not in response_properties:
                problems.append(f"Projection response missing field: {field}")

    if problems:
        print("Admin editorial operations HTTP contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Admin editorial operations HTTP contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

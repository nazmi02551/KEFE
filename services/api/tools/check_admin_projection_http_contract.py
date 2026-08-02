from __future__ import annotations

import json
from pathlib import Path

from export_openapi import load_expected_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
ADMIN_DIR = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
)
CONTRACT = CONTRACTS / "admin-editorial-operations-slice34.v1.json"
POLICY = CONTRACTS / "admin-http-surface.v1.yaml"
OPENAPI = CONTRACTS / "openapi.v1.json"
ROUTER = ADMIN_DIR / "editorial_projection_router.py"
REVIEW = ADMIN_DIR / "proposal_review.py"
PROJECTION = ADMIN_DIR / "editorial_projection.py"
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
REVIEW_PATH = "/internal/admin/v1/proposals/{proposal_id}/review"
PROJECTION_PATH = (
    "/internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection"
)
FORBIDDEN_FIELDS = {
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


def _operation(openapi: dict, path: str) -> dict | None:
    return openapi.get("paths", {}).get(path, {}).get("post")


def _request_fields(openapi: dict, operation: dict) -> set[str]:
    ref = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
        .rsplit("/", 1)[-1]
    )
    properties = (
        openapi.get("components", {})
        .get("schemas", {})
        .get(ref, {})
        .get("properties", {})
    )
    return set(properties)


def _has_csrf(operation: dict) -> bool:
    return any(
        parameter.get("in") == "header"
        and parameter.get("name", "").lower() == "x-kefe-csrf"
        for parameter in operation.get("parameters", [])
    )


def _require_fragments(
    problems: list[str],
    label: str,
    content: str,
    fragments: tuple[str, ...],
) -> None:
    for fragment in fragments:
        if fragment not in content:
            problems.append(f"{label} missing: {fragment}")


def main() -> int:
    required = (CONTRACT, POLICY, OPENAPI, ROUTER, REVIEW, PROJECTION, MAIN)
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required file: {path.relative_to(REPO_ROOT)}")
        return 1

    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    policy = POLICY.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    projection = PROJECTION.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    openapi = load_expected_contract(OPENAPI)

    if contract.get("capabilities") != [
        "CAP-061",
        "CAP-062",
        "CAP-063",
        "CAP-065",
    ]:
        problems.append("Slice 34 capability set/order is not locked")
    review_contract = contract.get("proposal_review", {})
    if review_contract.get("automatic_projection") is not False:
        problems.append("Proposal review must forbid automatic projection")
    projection_contract = contract.get("editorial_projection", {})
    if projection_contract.get("creates_lifecycle_state") != "DRAFT":
        problems.append("Editorial Projection must create DRAFT only")
    for field in (
        "automatic_submit",
        "automatic_authoring_review",
        "automatic_approval",
        "automatic_publication",
        "consumer_materialization",
    ):
        if projection_contract.get(field) is not False:
            problems.append(f"Editorial Projection must keep {field}=false")

    _require_fragments(
        problems,
        "Admin HTTP policy",
        policy,
        (
            "proposal_review_facade: SecuredProposalReviewService",
            "projection_facade: SecuredEditorialProjectionService",
            "path: /proposals/{proposal_id}/review",
            "automatic_projection: forbidden",
            "path: /candidate-proposals/{candidate_proposal_id}/projection",
            "capability: CONTENT_PROJECT",
            "creates_lifecycle_state: DRAFT",
        ),
    )
    _require_fragments(
        problems,
        "Admin editorial router",
        router,
        (
            'prefix="/internal/admin/v1"',
            '"/proposals/{proposal_id}/review"',
            '"/candidate-proposals/{candidate_proposal_id}/projection"',
            "class ProposalReviewRequest(StrictModel):",
            "class EditorialProjectionRequest(StrictModel):",
            "principal: WritePrincipalDep",
            "review.review(",
            "projection.project(",
            'lifecycle_state="DRAFT"',
        ),
    )
    _require_fragments(
        problems,
        "Proposal review service",
        review,
        (
            "AdminCapability.CONTENT_REVIEW",
            "reviewer_ref=principal.audit_actor_ref",
            "INGESTION_PROPOSAL_NOT_FOUND",
            "INGESTION_PROPOSAL_ALREADY_REVIEWED",
        ),
    )
    _require_fragments(
        problems,
        "Editorial Projection service",
        projection,
        (
            "AdminCapability.CONTENT_PROJECT",
            "requested_by_admin_ref=principal.audit_actor_ref",
            "EditorialProjectionCommand(",
        ),
    )

    for forbidden in (
        "EditorialProjectionService",
        "SecuredEditorialProjectionService",
        ".project(",
        ".publish(",
    ):
        if forbidden in review:
            problems.append(f"Proposal review service may not contain: {forbidden}")
    for forbidden in (
        "requested_by_admin_ref=body",
        "reviewer_ref=body",
        "actor_ref=body",
        ".publish(",
        ".approve(",
        ".submit_for_review(",
    ):
        if forbidden in router:
            problems.append(f"Admin editorial router may not contain: {forbidden}")
    if "app.include_router(admin_editorial_projection_router)" not in main_source:
        problems.append("Application does not include Admin editorial operations router")

    for path in (REVIEW_PATH, PROJECTION_PATH):
        operation = _operation(openapi, path)
        if operation is None:
            problems.append(f"OpenAPI missing POST {path}")
            continue
        if not _has_csrf(operation):
            problems.append(f"POST {path} is missing X-KEFE-CSRF")
        leaked = sorted(FORBIDDEN_FIELDS & _request_fields(openapi, operation))
        if leaked:
            problems.append(f"POST {path} accepts forbidden fields: {', '.join(leaked)}")

    if problems:
        print("Admin editorial operations HTTP contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Admin editorial operations HTTP contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

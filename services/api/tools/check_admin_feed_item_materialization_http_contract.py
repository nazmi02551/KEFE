from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
SERVICE = (
    API
    / "src/kefe_api/modules/admin_security/feed_item_materialization.py"
)
ROUTER = (
    API
    / "src/kefe_api/modules/admin_security/feed_item_materialization_router.py"
)
MAIN = API / "src/kefe_api/main.py"
MEMORY_TEST = API / "tests/test_admin_feed_item_materialization_http.py"
POSTGRES_TEST = (
    API / "tests/test_admin_feed_item_materialization_http_postgres.py"
)
ADR = (
    ROOT
    / "docs/adr/0093-secured-admin-feed-item-materialization-http-operation.md"
)
CONTRACT = (
    ROOT
    / "docs/contracts/admin-feed-item-materialization-http-slice57.v1.json"
)
OPENAPI = (
    ROOT
    / "docs/contracts/openapi-admin-feed-item-materialization.v0.19.overlay.json"
)
EXPORTER = (
    API / "tools/export_admin_feed_item_materialization_openapi_overlay.py"
)
OPENAPI_COMPOSER = API / "tools/export_openapi.py"
WORKFLOW = ROOT / ".github/workflows/admin-feed-item-materialization-ci.yml"

REQUIRED = (
    SERVICE,
    ROUTER,
    MAIN,
    MEMORY_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    OPENAPI,
    EXPORTER,
    OPENAPI_COMPOSER,
    WORKFLOW,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, ast.ClassDef)
    }


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def function(source: str, name: str) -> ast.FunctionDef:
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    fail(f"function {name} is missing")


def segment(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
    )


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing Admin feed item materialization files: {missing}")

    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    exporter = EXPORTER.read_text(encoding="utf-8")
    composer = OPENAPI_COMPOSER.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-feed-item-materialization-http-slice57":
        fail("Admin feed item materialization contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin feed item materialization contract is not accepted")
    http = contract.get("http", {})
    if http != {
        "method": "POST",
        "path": "/internal/admin/v1/feed-item-proposals/{proposal_id}/materialization",
        "request_fields": ["proposal_review_decision_id"],
        "success_status": 200,
        "response_fields": [
            "proposal_materialization_id",
            "proposal_id",
            "proposal_review_decision_id",
            "target_kind",
            "target_id",
            "replayed",
        ],
        "extra_request_fields": "forbidden",
    }:
        fail(f"Admin feed item materialization HTTP surface drifted: {http}")
    security = contract.get("security", {})
    if security.get("principal_dependency") != "WritePrincipalDep":
        fail("Admin materialization must use WritePrincipalDep")
    if security.get("capability") != "SOURCE_VERIFY":
        fail("Admin materialization capability drifted")
    for name in ("session_required", "csrf_required"):
        if security.get(name) is not True:
            fail(f"Admin materialization security invariant drifted: {name}")
    for name in ("review_endpoint_reused", "review_created_or_changed"):
        if security.get(name) is not False:
            fail(f"Admin materialization cannot create review authority: {name}")

    service_classes = class_map(service)
    for class_name in (
        "SecuredFeedItemMaterializationResult",
        "SecuredFeedItemMaterializationService",
    ):
        if class_name not in service_classes:
            fail(f"secured feed item materialization class missing: {class_name}")
    result_class = service_classes["SecuredFeedItemMaterializationResult"]
    if fields(result_class) != ("materialization", "replayed"):
        fail("secured feed item materialization result fields drifted")
    secured = service_classes["SecuredFeedItemMaterializationService"]
    materialize_source = segment(service, method(secured, "materialize"))
    ordered = (
        "self._security.authorize(",
        "self._repository.get_proposal(proposal_id)",
        "proposal.proposal_kind != PROPOSAL_KIND",
        "self._repository.get_review_decision(proposal_id)",
        "review.id != proposal_review_decision_id",
        "review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "self._repository.find_materialization(",
        "self._orchestration.materialize_accepted_proposal(",
        "return SecuredFeedItemMaterializationResult(",
    )
    positions = tuple(materialize_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(
        sorted(positions)
    ):
        fail("Admin materialization authorization/precondition/delegation order drifted")
    for fragment in (
        "AdminCapability.SOURCE_VERIFY",
        "materializer=self._materializer",
        "replayed=existing is not None",
        "materialization.review_decision_id != review.id",
        "materialization.target_kind != TARGET_KIND",
    ):
        if fragment not in materialize_source:
            fail(f"secured materialization guard missing: {fragment}")
    for error_code in (
        "ADMIN_FEED_ITEM_PROPOSAL_NOT_FOUND",
        "ADMIN_FEED_ITEM_REVIEW_REQUIRED",
        "ADMIN_FEED_ITEM_REVIEW_MISMATCH",
        "ADMIN_FEED_ITEM_REVIEW_NOT_ACCEPTED",
        "ADMIN_FEED_ITEM_PROPOSAL_SCHEMA_INVALID",
        "ADMIN_FEED_ITEM_MATERIALIZATION_CONFLICT",
    ):
        if error_code not in service:
            fail(f"bounded Admin materialization error missing: {error_code}")
    for forbidden in (
        "review_proposal(",
        "ProposalReviewDecision(",
        "SourceArtifact(",
        "NormalizedArtifact(",
        "payload[",
        "canonical_storage_ref",
        "sha256(",
        "add_claim(",
        "create_case",
        "project(",
        "publish(",
        "SecretAccess",
        "use_bytes",
        "requests",
        "httpx",
        "socket",
    ):
        if forbidden in service:
            fail(f"forbidden authority leaked into secured service: {forbidden}")

    router_classes = class_map(router)
    request_class = router_classes.get("FeedItemMaterializationRequest")
    response_class = router_classes.get("FeedItemMaterializationResponse")
    if request_class is None or fields(request_class) != (
        "proposal_review_decision_id",
    ):
        fail("Admin materialization request fields drifted")
    if response_class is None or fields(response_class) != (
        "proposal_materialization_id",
        "proposal_id",
        "proposal_review_decision_id",
        "target_kind",
        "target_id",
        "replayed",
    ):
        fail("Admin materialization response fields drifted")
    endpoint = function(router, "materialize_feed_item")
    endpoint_source = segment(router, endpoint)
    for fragment in (
        '"/feed-item-proposals/{proposal_id}/materialization"',
        "principal: WritePrincipalDep",
        "materialization: FeedItemMaterializationDep",
        "proposal_review_decision_id=body.proposal_review_decision_id",
        "replayed=result.replayed",
    ):
        if fragment not in router and fragment not in endpoint_source:
            fail(f"Admin materialization router invariant missing: {fragment}")
    if "status_code=" in router:
        fail("Admin materialization endpoint must use stable default HTTP 200")

    for fragment in (
        "SecuredFeedItemMaterializationService(",
        "app.state.secured_feed_item_materialization_service",
        "app.include_router(admin_feed_item_materialization_router)",
        "materializer=editorial_pipeline.feed_item_proposal_materializer",
    ):
        if fragment not in main_source:
            fail(f"Admin materialization application composition missing: {fragment}")
    if "secured_feed_item_materialization_service.materialize(" in main_source:
        fail("application startup cannot invoke feed item materialization")

    path = "/internal/admin/v1/feed-item-proposals/{proposal_id}/materialization"
    paths = openapi.get("paths", {})
    if set(paths) != {path}:
        fail(f"Admin materialization OpenAPI path drifted: {set(paths)}")
    post = paths[path].get("post", {})
    if set(post.get("responses", {})) != {"200", "422"}:
        fail("Admin materialization OpenAPI response statuses drifted")
    schemas = openapi.get("components", {}).get("schemas", {})
    if set(schemas) != {
        "FeedItemMaterializationRequest",
        "FeedItemMaterializationResponse",
    }:
        fail("Admin materialization OpenAPI schemas drifted")
    request_schema = schemas["FeedItemMaterializationRequest"]
    if request_schema.get("additionalProperties") is not False:
        fail("Admin materialization request must remain strict")
    if set(request_schema.get("properties", {})) != {
        "proposal_review_decision_id"
    }:
        fail("Admin materialization OpenAPI request fields drifted")
    if set(schemas["FeedItemMaterializationResponse"].get("properties", {})) != {
        "proposal_materialization_id",
        "proposal_id",
        "proposal_review_decision_id",
        "target_kind",
        "target_id",
        "replayed",
    }:
        fail("Admin materialization OpenAPI response fields drifted")
    for phrase in (
        "expected_schema_names",
        "expected_path_names",
        "Admin Feed Item materialization API must remain additive",
    ):
        if phrase not in exporter:
            fail(f"Admin materialization OpenAPI exporter guard missing: {phrase}")
    if "openapi-admin-feed-item-materialization.v0.19.overlay.json" not in composer:
        fail("Admin materialization overlay is not composed into OpenAPI drift gate")

    for test_name in (
        "test_accepted_feed_item_materialization_is_explicit_and_idempotent",
        "test_materialization_requires_session_csrf_and_source_verify_capability",
        "test_negative_review_and_wrong_review_id_fail_before_writes",
        "test_unreviewed_missing_and_wrong_schema_errors_are_bounded",
        "test_postgres_admin_feed_item_materialization_http_is_idempotent",
    ):
        if test_name not in tests:
            fail(f"Admin materialization test evidence missing: {test_name}")

    for phrase in (
        "strict request body contains only",
        "AdminCapability.SOURCE_VERIFY",
        "always returns HTTP 200",
        "Review remains a separate endpoint",
        "Raw payloads, raw storage references",
    ):
        if phrase not in adr:
            fail(f"ADR-0093 decision text missing: {phrase}")

    for phrase in (
        "Admin feed item materialization architecture fitness",
        "Admin feed item materialization HTTP behavior",
        "Admin feed item materialization PostgreSQL HTTP",
        "Admin feed item materialization OpenAPI exact gate",
        "Parent Admin HTTP architecture fitness",
        "Parent feed item materialization architecture fitness",
        "check_admin_feed_item_materialization_http_contract.py",
    ):
        if phrase not in workflow:
            fail(f"Admin materialization CI step missing: {phrase}")

    print("Admin feed item materialization HTTP contract: PASS")


if __name__ == "__main__":
    main()

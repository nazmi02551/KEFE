from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
SERVICE = API / "src/kefe_api/modules/admin_security/feed_item_materialization_status.py"
ROUTER = API / "src/kefe_api/modules/admin_security/proposal_queue_router.py"
MAIN = API / "src/kefe_api/main.py"
HTTP_TEST = API / "tests/test_admin_feed_item_materialization_status_http.py"
OPENAPI_TEST = API / "tests/test_admin_feed_item_materialization_status_openapi.py"
POSTGRES_TEST = API / "tests/test_admin_feed_item_materialization_status_postgres.py"
ADR = ROOT / "docs/adr/0092-secured-admin-feed-item-materialization-status.md"
CONTRACT = ROOT / "docs/contracts/admin-feed-item-materialization-status-slice56.v1.json"
POLICY = ROOT / "docs/contracts/admin-http-surface.v1.yaml"
ERRORS = ROOT / "docs/contracts/error-codes-admin-feed-item-status.v1.yaml"
OPENAPI_OVERLAY = ROOT / "docs/contracts/openapi-admin-feed-item-status.v0.19.overlay.json"
EXPORT = API / "tools/export_openapi.py"
WORKFLOW = ROOT / ".github/workflows/admin-feed-item-status-ci.yml"

REQUIRED = (
    SERVICE,
    ROUTER,
    MAIN,
    HTTP_TEST,
    OPENAPI_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    POLICY,
    ERRORS,
    OPENAPI_OVERLAY,
    EXPORT,
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


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
    )


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing Admin feed item status files: {missing}")

    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (HTTP_TEST, OPENAPI_TEST, POSTGRES_TEST)
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    policy = POLICY.read_text(encoding="utf-8")
    errors = ERRORS.read_text(encoding="utf-8")
    overlay = json.loads(OPENAPI_OVERLAY.read_text(encoding="utf-8"))
    export = EXPORT.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-feed-item-materialization-status-slice56":
        fail("Admin feed item status contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin feed item status contract is not accepted")

    exact_path = "/internal/admin/v1/proposals/{proposal_id}/feed-item-materialization-status"
    http = contract.get("http", {})
    if http.get("method") != "GET" or http.get("path") != exact_path:
        fail("Admin feed item status HTTP identity drifted")
    if http.get("read_principal_required") is not True or http.get("csrf_required") is not False:
        fail("Admin feed item status read/CSRF boundary drifted")
    if http.get("response_fields") != [
        "materialized_at",
        "proposal_id",
        "proposal_materialization_id",
        "proposal_review_decision",
        "proposal_review_decision_id",
        "status",
        "target_id",
        "target_kind",
    ]:
        fail("Admin feed item status response fields drifted")
    for key in (
        "response_includes_payload",
        "response_includes_normalized_text",
        "response_includes_evidence",
    ):
        if http.get(key) is not False:
            fail(f"Admin feed item status disclosure drifted: {key}")

    authorization = contract.get("authorization", {})
    if authorization.get("required_capabilities") != ["CONTENT_REVIEW", "SOURCE_VERIFY"]:
        fail("Admin feed item status capabilities drifted")
    if authorization.get("editor_only_allowed") is not False:
        fail("Editor-only Admin cannot read feed item status")
    if authorization.get("publisher_only_allowed") is not False:
        fail("Publisher-only Admin cannot read feed item status")

    states = contract.get("states", {})
    if set(states) != {"REVIEW_REQUIRED", "READY", "MATERIALIZED"}:
        fail("Admin feed item status state set drifted")
    if states["MATERIALIZED"].get("target_kind") != "NORMALIZED_ARTIFACT":
        fail("MATERIALIZED target kind drifted")
    if states["MATERIALIZED"].get("review_binding_exact") is not True:
        fail("MATERIALIZED review binding drifted")

    service_tree = ast.parse(service)
    classes = class_map(service)
    enum_node = classes.get("FeedItemMaterializationStatus")
    snapshot = classes.get("FeedItemMaterializationStatusSnapshot")
    secured = classes.get("SecuredFeedItemMaterializationStatusService")
    if enum_node is None or snapshot is None or secured is None:
        fail("Admin feed item status classes are missing")
    enum_values = {
        child.targets[0].id: child.value.value
        for child in enum_node.body
        if isinstance(child, ast.Assign)
        and isinstance(child.targets[0], ast.Name)
        and isinstance(child.value, ast.Constant)
    }
    if enum_values != {
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
        "READY": "READY",
        "MATERIALIZED": "MATERIALIZED",
    }:
        fail(f"Admin feed item status enum drifted: {enum_values}")
    expected_fields = (
        "proposal_id",
        "status",
        "proposal_review_decision_id",
        "proposal_review_decision",
        "proposal_materialization_id",
        "target_kind",
        "target_id",
        "materialized_at",
    )
    if fields(snapshot) != expected_fields:
        fail("Admin feed item status snapshot fields drifted")

    observe = method(secured, "observe")
    observe_source = ast.get_source_segment(service, observe) or ""
    ordered = (
        "AdminCapability.CONTENT_REVIEW",
        "AdminCapability.SOURCE_VERIFY",
        "self._repository.get_proposal(proposal_id)",
        "self._repository.get_review_decision(proposal_id)",
        "self._repository.find_materialization(proposal_id)",
    )
    positions = tuple(observe_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
        fail("Admin feed item status observation order drifted")
    for fragment in (
        "proposal.proposal_kind != _FEED_ITEM_KIND",
        "proposal.payload_schema_ref != _FEED_ITEM_SCHEMA_REF",
        "proposal.payload_schema_version != _FEED_ITEM_SCHEMA_VERSION",
        "proposal.risk_code != _FEED_ITEM_RISK_CODE",
        "proposal.ai_execution_ref is not None",
        "materialization.target_kind != _TARGET_KIND",
        "review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "materialization.review_decision_id != review.id",
        "FeedItemMaterializationStatus.MATERIALIZED",
        "FeedItemMaterializationStatus.READY",
        "FeedItemMaterializationStatus.REVIEW_REQUIRED",
        "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT",
    ):
        if fragment not in observe_source:
            fail(f"Admin feed item status guard missing: {fragment}")

    if any(
        isinstance(node, ast.Attribute) and node.attr == "payload"
        for node in ast.walk(observe)
    ):
        fail("Admin feed item status cannot read proposal payload")
    for forbidden in (
        "KnowledgeProposalMaterializer",
        "materialize_accepted_proposal(",
        "review_proposal(",
        "add_materialization(",
        "get_normalized_artifact(",
        "source_evidence",
        "create_case",
        "project(",
        "publish(",
        "requests",
        "httpx",
        "socket",
    ):
        if forbidden in service:
            fail(f"forbidden behavior leaked into status service: {forbidden}")

    router_classes = class_map(router)
    response = router_classes.get("FeedItemMaterializationStatusResponse")
    if response is None or fields(response) != expected_fields:
        fail("FeedItemMaterializationStatusResponse fields drifted")
    for fragment in (
        '"/proposals/{proposal_id}/feed-item-materialization-status"',
        "principal: ReadPrincipalDep",
        "status_service: FeedItemMaterializationStatusDep",
        "status_service.observe(principal, proposal_id=proposal_id)",
        "status=snapshot.status.value",
    ):
        if fragment not in router:
            fail(f"Admin feed item status router contract missing: {fragment}")
    for forbidden in (
        "KnowledgeProposalMaterializer",
        "NormalizedArtifact",
        "add_materialization(",
        "materialize_accepted_proposal(",
    ):
        if forbidden in router:
            fail(f"forbidden mutation leaked into status router: {forbidden}")
    if "app.include_router(admin_proposal_queue_router)" not in main_source:
        fail("Admin proposal/status router is not composed")

    for fragment in (
        "feed_item_materialization_status_facade: SecuredFeedItemMaterializationStatusService",
        "path: /proposals/{proposal_id}/feed-item-materialization-status",
        "capabilities: [CONTENT_REVIEW, SOURCE_VERIFY]",
        "states: [REVIEW_REQUIRED, READY, MATERIALIZED]",
        "payload_disclosure: forbidden",
        "mutation: forbidden",
    ):
        if fragment not in policy:
            fail(f"Admin HTTP policy missing status boundary: {fragment}")
    if "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT" not in errors:
        fail("Admin feed item status error registry is missing conflict code")

    if overlay.get("target_version") != "0.19.0":
        fail("Admin feed item status OpenAPI target version drifted")
    if set(overlay.get("paths", {})) != {exact_path}:
        fail("Admin feed item status OpenAPI path set drifted")
    schemas = overlay.get("components", {}).get("schemas", {})
    if set(schemas) != {"FeedItemMaterializationStatusResponse"}:
        fail("Admin feed item status OpenAPI schema set drifted")
    if '"openapi-admin-feed-item-status.v0.19.overlay.json"' not in export:
        fail("Admin feed item status OpenAPI overlay is not composed")

    for test_name in (
        "test_status_requires_auth_and_both_capabilities_without_csrf",
        "test_status_progresses_review_required_ready_materialized",
        "test_rejected_unsupported_and_conflicting_statuses_are_bounded",
        "test_feed_item_materialization_status_openapi_is_exact_and_bounded",
        "test_postgres_status_progression_and_conflict_are_persisted",
    ):
        if test_name not in tests:
            fail(f"Admin feed item status test evidence missing: {test_name}")
    for phrase in (
        "Add one read-only additive endpoint",
        "Three persisted states",
        "Fail closed on inconsistent persisted state",
        "Bounded response",
        "No mutation or automation",
    ):
        if phrase not in adr:
            fail(f"ADR-0092 decision text missing: {phrase}")
    for phrase in (
        "Admin feed item status architecture fitness",
        "Admin feed item status HTTP behavior",
        "Admin feed item status PostgreSQL behavior",
        "Parent Admin feed item materialization architecture fitness",
        "Parent Admin Proposal queue HTTP behavior",
        "check_admin_feed_item_materialization_status_contract.py",
    ):
        if phrase not in workflow:
            fail(f"Admin feed item status CI step missing: {phrase}")

    print("Admin feed item materialization status contract: PASS")


if __name__ == "__main__":
    main()

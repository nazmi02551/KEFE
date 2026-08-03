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
    / "src/kefe_api/modules/admin_security/editorial_projection_router.py"
)
MAIN = API / "src/kefe_api/main.py"
HTTP_TEST = API / "tests/test_admin_feed_item_materialization_http.py"
OPENAPI_TEST = API / "tests/test_admin_feed_item_materialization_openapi.py"
POSTGRES_TEST = API / "tests/test_admin_feed_item_materialization_postgres.py"
ADR = ROOT / "docs/adr/0091-secured-admin-feed-item-materialization-command.md"
CONTRACT = ROOT / "docs/contracts/admin-feed-item-materialization-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/admin-feed-item-materialization-ci.yml"

REQUIRED = (
    SERVICE,
    ROUTER,
    MAIN,
    HTTP_TEST,
    OPENAPI_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
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
    tests = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (HTTP_TEST, OPENAPI_TEST, POSTGRES_TEST)
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-feed-item-materialization-slice55":
        fail("Admin feed item materialization contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin feed item materialization contract is not accepted")

    http = contract.get("http", {})
    if http.get("method") != "POST":
        fail("Admin feed item materialization method drifted")
    if http.get("path") != (
        "/internal/admin/v1/proposals/{proposal_id}/feed-item-materialization"
    ):
        fail("Admin feed item materialization path drifted")
    if http.get("write_principal_required") is not True:
        fail("Admin feed item materialization must require write principal")
    if http.get("csrf_required") is not True:
        fail("Admin feed item materialization must require CSRF")
    if http.get("request_fields") != ["proposal_review_decision_id"]:
        fail("Admin feed item materialization request fields drifted")
    if http.get("response_fields") != [
        "materialized_at",
        "proposal_id",
        "proposal_materialization_id",
        "proposal_review_decision_id",
        "target_id",
        "target_kind",
    ]:
        fail("Admin feed item materialization response fields drifted")
    if http.get("response_includes_payload") is not False:
        fail("Admin feed item materialization response cannot expose payload")
    if http.get("response_includes_evidence_bytes") is not False:
        fail("Admin feed item materialization cannot expose evidence bytes")

    authorization = contract.get("authorization", {})
    if authorization.get("required_capabilities") != [
        "CONTENT_REVIEW",
        "SOURCE_VERIFY",
    ]:
        fail("Admin feed item materialization capability set drifted")
    if authorization.get("editor_only_allowed") is not False:
        fail("Editor-only Admin cannot materialize feed items")
    if authorization.get("publisher_only_allowed") is not False:
        fail("Publisher-only Admin cannot materialize feed items")

    proposal_scope = contract.get("proposal_scope", {})
    expected_scope = {
        "kind": "FEED_ITEM",
        "payload_schema_ref": "kefe.feed-item",
        "payload_schema_version": "1.0.0",
        "risk_code": "UNREVIEWED_EXTERNAL_FEED_ITEM",
        "ai_execution_ref_allowed": False,
        "generic_materialization_exposed": False,
    }
    if proposal_scope != expected_scope:
        fail(f"Admin feed item proposal scope drifted: {proposal_scope}")

    service_classes = class_map(service)
    secured = service_classes.get("SecuredFeedItemMaterializationService")
    if secured is None:
        fail("SecuredFeedItemMaterializationService is missing")
    materialize = method(secured, "materialize")
    materialize_source = ast.get_source_segment(service, materialize) or ""
    ordered = (
        "AdminCapability.CONTENT_REVIEW",
        "AdminCapability.SOURCE_VERIFY",
        "self._repository.get_proposal(proposal_id)",
        "self._repository.get_review_decision(proposal_id)",
        "self._repository.find_materialization(",
        "KnowledgeProposalMaterializer(",
        "self._orchestration.materialize_accepted_proposal(",
    )
    positions = tuple(materialize_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(
        sorted(positions)
    ):
        fail("Admin feed item materialization execution order drifted")
    for fragment in (
        "proposal.proposal_kind != _FEED_ITEM_KIND",
        "proposal.payload_schema_ref != _FEED_ITEM_SCHEMA_REF",
        "proposal.payload_schema_version != _FEED_ITEM_SCHEMA_VERSION",
        "proposal.risk_code != _FEED_ITEM_RISK_CODE",
        "proposal.ai_execution_ref is not None",
        "review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "review.id != proposal_review_decision_id",
        "existing.review_decision_id != review.id",
        "materialization.target_kind != _TARGET_KIND",
        "INGESTION_FEED_ITEM_MATERIALIZATION_UNSUPPORTED",
        "INGESTION_PROPOSAL_REVIEW_NOT_ACCEPTED",
        "INGESTION_PROPOSAL_REVIEW_BINDING_MISMATCH",
        "INGESTION_FEED_ITEM_MATERIALIZATION_CONFLICT",
        "INGESTION_FEED_ITEM_MATERIALIZATION_INVALID",
    ):
        if fragment not in materialize_source:
            fail(f"Admin feed item materialization guard missing: {fragment}")

    for forbidden in (
        "NormalizedArtifact",
        "add_normalized_artifact(",
        "review_proposal(",
        "create_case",
        "project(",
        "publish(",
        "requests",
        "httpx",
        "socket",
        "openai",
    ):
        if forbidden in service:
            fail(f"forbidden behavior leaked into secured materialization: {forbidden}")

    router_classes = class_map(router)
    request_model = router_classes.get("FeedItemMaterializationRequest")
    response_model = router_classes.get("FeedItemMaterializationResponse")
    if request_model is None or fields(request_model) != (
        "proposal_review_decision_id",
    ):
        fail("FeedItemMaterializationRequest fields drifted")
    if response_model is None or fields(response_model) != (
        "proposal_materialization_id",
        "proposal_id",
        "proposal_review_decision_id",
        "target_kind",
        "target_id",
        "materialized_at",
    ):
        fail("FeedItemMaterializationResponse fields drifted")
    for fragment in (
        '"/proposals/{proposal_id}/feed-item-materialization"',
        "principal: WritePrincipalDep",
        "materialization: FeedItemMaterializationDep",
        "materialization.materialize(",
        "proposal_review_decision_id=body.proposal_review_decision_id",
        "proposal_materialization_id=record.id",
        "proposal_review_decision_id=record.review_decision_id",
    ):
        if fragment not in router:
            fail(f"Admin feed item router contract missing: {fragment}")
    for forbidden in (
        "NormalizedArtifact",
        "KnowledgeProposalMaterializer",
        "add_normalized_artifact(",
        '"/proposals/{proposal_id}/materialize"',
    ):
        if forbidden in router:
            fail(f"forbidden construction/generic route leaked into router: {forbidden}")

    if "app.include_router(admin_editorial_projection_router)" not in main_source:
        fail("Admin editorial projection/materialization router is not composed")

    for test_name in (
        "test_command_requires_auth_csrf_and_both_reviewer_capabilities",
        "test_accepted_command_is_bounded_idempotent_and_persists_exact_target",
        "test_rejected_unsupported_and_conflicting_commands_fail_bounded",
        "test_feed_item_materialization_openapi_is_exact_and_bounded",
        "test_secured_postgres_command_authorizes_and_replays_one_materialization",
        "test_secured_postgres_command_reports_not_found_without_materialization",
    ):
        if test_name not in tests:
            fail(f"Admin feed item materialization test evidence missing: {test_name}")

    for phrase in (
        "One exact internal command",
        "Review remains a separate prior command",
        "Security boundary",
        "Existing materializer remains authoritative",
        "Production boundaries",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")

    for phrase in (
        "Admin feed item materialization architecture fitness",
        "Admin feed item materialization HTTP behavior",
        "Admin feed item materialization PostgreSQL behavior",
        "Parent feed item normalization architecture fitness",
        "Parent Admin Proposal queue HTTP behavior",
        "check_admin_feed_item_materialization_contract.py",
    ):
        if phrase not in workflow:
            fail(f"Admin feed item materialization CI step missing: {phrase}")

    print("Admin feed item materialization contract: PASS")


if __name__ == "__main__":
    main()

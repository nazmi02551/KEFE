from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
SERVICE = API / "src/kefe_api/modules/admin_security/feed_item_review.py"
ROUTER = API / "src/kefe_api/modules/admin_security/feed_item_review_router.py"
MAIN = API / "src/kefe_api/main.py"
MEMORY_TEST = API / "tests/test_admin_feed_item_review_http.py"
POSTGRES_TEST = API / "tests/test_admin_feed_item_review_http_postgres.py"
ADR = ROOT / "docs/adr/0090-evidence-safe-admin-feed-item-review-surface.md"
CONTRACT = ROOT / "docs/contracts/admin-feed-item-review-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/admin-feed-item-review-ci.yml"

REQUIRED = (
    SERVICE,
    ROUTER,
    MAIN,
    MEMORY_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)
EXPECTED_NEW_SCHEMAS = {
    "FeedItemReviewDecisionResponse",
    "FeedItemReviewDetailResponse",
    "FeedItemReviewPageResponse",
    "FeedItemReviewSummaryResponse",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    tree = ast.parse(source)
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
    )


def _openapi(version: str) -> dict[str, Any]:
    from kefe_api.core.settings import get_settings
    from kefe_api.main import create_app

    previous = os.environ.get("KEFE_API_VERSION")
    os.environ["KEFE_API_VERSION"] = version
    get_settings.cache_clear()
    try:
        return create_app().openapi()
    finally:
        if previous is None:
            os.environ.pop("KEFE_API_VERSION", None)
        else:
            os.environ["KEFE_API_VERSION"] = previous
        get_settings.cache_clear()


def _properties(
    schema_name: str,
    schemas: dict[str, Any],
    *,
    seen: frozenset[str] = frozenset(),
) -> set[str]:
    if schema_name in seen:
        fail(f"recursive OpenAPI schema detected: {schema_name}")
    schema = schemas[schema_name]
    names = set(schema.get("properties", {}))
    for item in schema.get("allOf", []):
        reference = item.get("$ref")
        if reference:
            parent = reference.rsplit("/", 1)[-1]
            names |= _properties(parent, schemas, seen=seen | {schema_name})
        names |= set(item.get("properties", {}))
    return names


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing Admin feed item review files: {missing}")

    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-feed-item-review-slice54":
        fail("Admin feed item review contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin feed item review contract is not accepted")
    api = contract.get("api", {})
    if api.get("minimum_version") != "0.21.0":
        fail("Admin feed item review minimum API version drifted")
    if api.get("mutation_endpoint_added") is not False:
        fail("Admin feed item review cannot add a mutation endpoint")
    if api.get("raw_evidence_dereference_endpoint_added") is not False:
        fail("Admin feed item review cannot add evidence dereference")

    source_contract = contract.get("source_contract", {})
    expected_source = {
        "proposal_kind": "FEED_ITEM",
        "payload_schema_ref": "kefe.feed-item",
        "payload_schema_version": "1.0.0",
        "pipeline_code": "RSS_ATOM_FEED_ITEM_EXTRACTION",
        "pipeline_version": "1.0.0",
        "risk_code": "UNREVIEWED_EXTERNAL_FEED_ITEM",
        "input_artifact_kind": "SOURCE_ARTIFACT",
    }
    for key, value in expected_source.items():
        if source_contract.get(key) != value:
            fail(f"Admin feed item source contract drifted: {key}")

    service_classes = class_map(service)
    for name in (
        "FeedItemReviewPayload",
        "FeedItemReviewRecord",
        "FeedItemReviewPage",
        "SecuredFeedItemReviewService",
    ):
        if name not in service_classes:
            fail(f"Admin feed item review class is missing: {name}")
    payload_fields = fields(service_classes["FeedItemReviewPayload"])
    if payload_fields != (
        "source_artifact_id",
        "feed_content_hash",
        "feed_storage_ref",
        "feed_format",
        "feed_title",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "summary_text",
    ):
        fail(f"FeedItemReviewPayload fields drifted: {payload_fields}")

    for fragment in (
        "proposal_kind=PROPOSAL_KIND",
        "risk_code=RISK_CODE",
        "pipeline_code=PIPELINE_CODE",
        "frozenset(payload) != _PAYLOAD_KEYS",
        "canonical_storage_ref(content_hash)",
        "payload.source_artifact_id != run.input_artifact_id",
        "payload.feed_content_hash != run.input_content_hash",
        "proposal.provenance_ref != payload.feed_storage_ref",
        "artifact.raw_storage_ref != payload.feed_storage_ref",
        "ADMIN_FEED_ITEM_CONTRACT_INVALID",
        "ADMIN_FEED_ITEM_NOT_FOUND",
    ):
        if fragment not in service:
            fail(f"Admin feed item review invariant missing: {fragment}")

    forbidden_service = (
        "RawSourceEvidenceReader",
        "RawSourceEvidenceStore",
        "read_owned_copy",
        "read_exact(",
        ".seal(",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "project(",
        "publish(",
    )
    for fragment in forbidden_service:
        if fragment in service:
            fail(f"forbidden authority leaked into Admin feed read adapter: {fragment}")

    router_classes = class_map(router)
    for name in EXPECTED_NEW_SCHEMAS:
        if name not in router_classes:
            fail(f"Admin feed item response schema missing: {name}")
    for fragment in (
        '@router.get("/feed-items"',
        '"/feed-items/{proposal_id}"',
        "response_model=FeedItemReviewPageResponse",
        "response_model=FeedItemReviewDetailResponse",
        "repository=request.app.state.proposal_review_queue_repository",
        "knowledge=request.app.state.knowledge_repository",
    ):
        if fragment not in router:
            fail(f"Admin feed item router invariant missing: {fragment}")
    for mutation in ("@router.post", "@router.put", "@router.patch", "@router.delete"):
        if mutation in router:
            fail(f"Admin feed item router cannot mutate: {mutation}")
    if "payload:" in router or "raw_body" in router or "raw_bytes" in router:
        fail("Admin feed item response cannot expose arbitrary/raw payload")

    if "if _api_at_least(settings.api_version, 0, 21):" not in main_source:
        fail("Admin feed item router must be API 0.21 gated")
    if "app.include_router(admin_feed_item_review_router)" not in main_source:
        fail("Admin feed item router is not composed")

    for test_name in (
        "test_surface_is_additive_at_021_and_authorized",
        "test_detail_hides_other_kinds_and_rejects_contract_drift",
        "test_postgres_feed_item_review_list_detail_and_review_refresh",
    ):
        if test_name not in tests:
            fail(f"Admin feed item test evidence missing: {test_name}")

    for phrase in (
        "typed feed-review contract",
        "payload key set is exact",
        "no dereference endpoint",
        "Human review remains mandatory",
        "API 0.21",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "Admin feed item review architecture and OpenAPI fitness",
        "Admin feed item review memory HTTP",
        "Admin feed item review PostgreSQL HTTP",
        "Parent feed item extraction architecture fitness",
        "Parent Admin Proposal queue architecture fitness",
    ):
        if phrase not in workflow:
            fail(f"Admin feed item CI step missing: {phrase}")

    old = _openapi("0.20.0")
    new = _openapi("0.21.0")
    list_path = api["list_path"]
    detail_path = api["detail_path"]
    if list_path in old.get("paths", {}) or detail_path in old.get("paths", {}):
        fail("Admin feed item paths leaked into API 0.20")

    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})
    added_paths = set(new_paths) - set(old_paths)
    if added_paths != {list_path, detail_path}:
        fail(f"API 0.21 path additions drifted: {sorted(added_paths)}")
    for path, definition in old_paths.items():
        if new_paths.get(path) != definition:
            fail(f"API 0.21 changed existing path: {path}")
    for path in (list_path, detail_path):
        if set(new_paths[path]) != {"get"}:
            fail(f"Admin feed item path must be GET-only: {path}")

    old_schemas = old.get("components", {}).get("schemas", {})
    new_schemas = new.get("components", {}).get("schemas", {})
    added_schemas = set(new_schemas) - set(old_schemas)
    if added_schemas != EXPECTED_NEW_SCHEMAS:
        fail(f"API 0.21 schema additions drifted: {sorted(added_schemas)}")
    for name, definition in old_schemas.items():
        if new_schemas.get(name) != definition:
            fail(f"API 0.21 changed existing schema: {name}")

    expected_summary = set(contract["list_response_fields"])
    expected_detail = expected_summary | set(contract["detail_additional_fields"])
    if _properties("FeedItemReviewSummaryResponse", new_schemas) != expected_summary:
        fail("Feed item summary OpenAPI fields drifted")
    if _properties("FeedItemReviewDetailResponse", new_schemas) != expected_detail:
        fail("Feed item detail OpenAPI fields drifted")
    if _properties("FeedItemReviewPageResponse", new_schemas) != {
        "items",
        "next_cursor",
    }:
        fail("Feed item page OpenAPI fields drifted")

    forbidden_fields = set(contract["forbidden_response_fields"])
    for name in EXPECTED_NEW_SCHEMAS:
        leaked = _properties(name, new_schemas) & forbidden_fields
        if leaked:
            fail(f"forbidden Admin feed item OpenAPI fields leaked: {sorted(leaked)}")

    list_parameters = {
        item["name"] for item in new_paths[list_path]["get"].get("parameters", [])
    }
    if list_parameters != {"limit", "cursor", "review_state", "run_id"}:
        fail(f"Admin feed item list parameters drifted: {sorted(list_parameters)}")
    detail_parameters = {
        item["name"] for item in new_paths[detail_path]["get"].get("parameters", [])
    }
    if detail_parameters != {"proposal_id"}:
        fail(f"Admin feed item detail parameters drifted: {sorted(detail_parameters)}")

    print("Admin feed item review contract and OpenAPI: PASS")


if __name__ == "__main__":
    main()

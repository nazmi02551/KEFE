from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
SERVICE = API / "src/kefe_api/modules/admin_security/source_brief_review.py"
ROUTER = API / "src/kefe_api/modules/admin_security/source_brief_review_router.py"
MAIN = API / "src/kefe_api/main.py"
MEMORY_TEST = API / "tests/test_admin_source_brief_review_http.py"
POSTGRES_TEST = API / "tests/test_admin_source_brief_review_http_postgres.py"
ADR = ROOT / "docs/adr/0092-lineage-safe-admin-source-brief-review-surface.md"
CONTRACT = ROOT / "docs/contracts/admin-source-brief-review-slice56.v1.json"
WORKFLOW = ROOT / ".github/workflows/admin-source-brief-review-ci.yml"

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
EXPECTED_SCHEMAS = {
    "SourceBriefReviewDecisionResponse",
    "SourceBriefReviewDetailResponse",
    "SourceBriefReviewPageResponse",
    "SourceBriefReviewSummaryResponse",
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
        fail(f"missing Admin Source Brief review files: {missing}")

    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-source-brief-review-slice56":
        fail("Admin Source Brief review contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin Source Brief review contract is not accepted")
    api = contract.get("api", {})
    if api.get("minimum_version") != "0.23.0":
        fail("Admin Source Brief review minimum API version drifted")
    if api.get("mutation_endpoint_added") is not False:
        fail("Admin Source Brief review cannot add mutation endpoints")
    if api.get("evidence_dereference_endpoint_added") is not False:
        fail("Admin Source Brief review cannot add evidence dereference")

    source_contract = contract.get("source_contract", {})
    expected_source = {
        "proposal_kind": "SOURCE_BRIEF",
        "payload_schema_ref": "kefe.source-brief",
        "payload_schema_version": "1.0.0",
        "pipeline_code": "FEED_ITEM_SOURCE_BRIEF",
        "pipeline_version": "1.0.0",
        "risk_code": "UNREVIEWED_SOURCE_BRIEF",
        "input_artifact_kind": "NORMALIZED_ARTIFACT",
    }
    for key, value in expected_source.items():
        if source_contract.get(key) != value:
            fail(f"Admin Source Brief source contract drifted: {key}")

    service_classes = class_map(service)
    for name in (
        "SourceBriefReviewPayload",
        "SourceBriefReviewRecord",
        "SourceBriefReviewPage",
        "SecuredSourceBriefReviewService",
    ):
        if name not in service_classes:
            fail(f"Admin Source Brief review class missing: {name}")
    payload_fields = fields(service_classes["SourceBriefReviewPayload"])
    if payload_fields != (
        "normalized_artifact_id",
        "parent_feed_item_proposal_id",
        "review_decision_id",
        "source_artifact_id",
        "source_content_hash",
        "evidence_ref",
        "feed_format",
        "publisher_or_issuer",
        "headline",
        "source_url",
        "published_at",
        "synopsis",
        "language_code",
        "jurisdiction_code",
    ):
        fail(f"SourceBriefReviewPayload fields drifted: {payload_fields}")

    for fragment in (
        "proposal_kind=SOURCE_BRIEF_KIND",
        "risk_code=SOURCE_BRIEF_RISK_CODE",
        "pipeline_code=PIPELINE_CODE",
        "frozenset(payload) != _PAYLOAD_KEYS",
        "run.input_artifact_kind is not InputArtifactKind.NORMALIZED_ARTIFACT",
        "payload.normalized_artifact_id != run.input_artifact_id",
        "proposal.provenance_ref != payload.evidence_ref",
        "self._knowledge.get_normalized_artifact(",
        "require_source_brief_normalized_artifact(normalized)",
        "self._feed_items.detail(",
        "ProposalReviewDecisionKind.ACCEPTED",
        "metadata.feed_storage_ref != payload.evidence_ref",
        "ADMIN_SOURCE_BRIEF_CONTRACT_INVALID",
        "ADMIN_SOURCE_BRIEF_NOT_FOUND",
    ):
        if fragment not in service:
            fail(f"Admin Source Brief review invariant missing: {fragment}")

    for fragment in (
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
        "create_case",
        "project(",
        "publish(",
    ):
        if fragment in service:
            fail(f"forbidden authority leaked into Source Brief review: {fragment}")

    router_classes = class_map(router)
    for name in EXPECTED_SCHEMAS:
        if name not in router_classes:
            fail(f"Source Brief response schema missing: {name}")
    for fragment in (
        '@router.get("/source-briefs"',
        '"/source-briefs/{proposal_id}"',
        "response_model=SourceBriefReviewPageResponse",
        "response_model=SourceBriefReviewDetailResponse",
        "feed_items=get_feed_item_review(request)",
        "knowledge=request.app.state.knowledge_repository",
    ):
        if fragment not in router:
            fail(f"Source Brief router invariant missing: {fragment}")
    for mutation in ("@router.post", "@router.put", "@router.patch", "@router.delete"):
        if mutation in router:
            fail(f"Source Brief review router cannot mutate: {mutation}")
    if "payload:" in router or "raw_body" in router or "raw_bytes" in router:
        fail("Source Brief response cannot expose arbitrary/raw payload")

    if "if _api_at_least(settings.api_version, 0, 23):" not in main_source:
        fail("Source Brief review router must be API 0.23 gated")
    if "app.include_router(admin_source_brief_review_router)" not in main_source:
        fail("Source Brief review router is not composed")

    for test_name in (
        "test_source_brief_review_surface_is_023_typed_and_refreshes_review",
        "test_source_brief_detail_hides_other_kind_and_rejects_payload_drift",
        "test_postgres_source_brief_review_list_detail_and_review_refresh",
    ):
        if test_name not in tests:
            fail(f"Source Brief review test evidence missing: {test_name}")
    for phrase in (
        "typed contract",
        "payload key set is exact",
        "accepted feed item",
        "API 0.22 remains unchanged",
        "only mutation",
    ):
        if phrase not in adr:
            fail(f"ADR-0092 decision text missing: {phrase}")
    for phrase in (
        "Admin Source Brief review architecture and OpenAPI fitness",
        "Admin Source Brief review memory HTTP",
        "Admin Source Brief review PostgreSQL HTTP",
        "Parent Source Brief ingestion architecture fitness",
        "Parent Admin feed item review architecture fitness",
    ):
        if phrase not in workflow:
            fail(f"Admin Source Brief review CI step missing: {phrase}")

    old = _openapi("0.22.0")
    new = _openapi("0.23.0")
    list_path = api["list_path"]
    detail_path = api["detail_path"]
    if list_path in old.get("paths", {}) or detail_path in old.get("paths", {}):
        fail("Source Brief review paths leaked into API 0.22")
    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})
    if set(new_paths) - set(old_paths) != {list_path, detail_path}:
        fail("API 0.23 path additions drifted")
    for path, definition in old_paths.items():
        if new_paths.get(path) != definition:
            fail(f"API 0.23 changed existing path: {path}")
    for path in (list_path, detail_path):
        if set(new_paths[path]) != {"get"}:
            fail(f"Source Brief review path must be GET-only: {path}")

    old_schemas = old.get("components", {}).get("schemas", {})
    new_schemas = new.get("components", {}).get("schemas", {})
    if set(new_schemas) - set(old_schemas) != EXPECTED_SCHEMAS:
        fail("API 0.23 schema additions drifted")
    for name, definition in old_schemas.items():
        if new_schemas.get(name) != definition:
            fail(f"API 0.23 changed existing schema: {name}")

    summary_fields = _properties("SourceBriefReviewSummaryResponse", new_schemas)
    detail_fields = _properties("SourceBriefReviewDetailResponse", new_schemas)
    if summary_fields != set(contract["list_response_fields"]):
        fail(f"Source Brief summary OpenAPI fields drifted: {sorted(summary_fields)}")
    expected_detail = set(contract["list_response_fields"]) | set(
        contract["detail_additional_fields"]
    )
    if detail_fields != expected_detail:
        fail(f"Source Brief detail OpenAPI fields drifted: {sorted(detail_fields)}")
    if _properties("SourceBriefReviewPageResponse", new_schemas) != {
        "items",
        "next_cursor",
    }:
        fail("Source Brief page OpenAPI fields drifted")

    forbidden_fields = set(contract["forbidden_response_fields"])
    for name in EXPECTED_SCHEMAS:
        leaked = _properties(name, new_schemas) & forbidden_fields
        if leaked:
            fail(f"forbidden Source Brief response fields leaked: {sorted(leaked)}")

    list_parameters = {
        item["name"] for item in new_paths[list_path]["get"].get("parameters", [])
    }
    if list_parameters != {"limit", "cursor", "review_state", "run_id"}:
        fail(f"Source Brief list parameters drifted: {sorted(list_parameters)}")
    detail_parameters = {
        item["name"] for item in new_paths[detail_path]["get"].get("parameters", [])
    }
    if detail_parameters != {"proposal_id"}:
        fail(f"Source Brief detail parameters drifted: {sorted(detail_parameters)}")

    print("Admin Source Brief review contract and OpenAPI: PASS")


if __name__ == "__main__":
    main()

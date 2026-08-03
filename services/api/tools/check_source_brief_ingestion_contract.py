from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
STAGE = API / "src/kefe_api/modules/ingestion_orchestration/source_brief_ingestion.py"
SERVICE = API / "src/kefe_api/modules/admin_security/source_brief_ingestion.py"
ROUTER = API / "src/kefe_api/modules/admin_security/source_brief_ingestion_router.py"
MODELS = API / "src/kefe_api/modules/ingestion_orchestration/models.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
MEMORY_TEST = API / "tests/test_source_brief_ingestion_http.py"
POSTGRES_TEST = API / "tests/test_source_brief_ingestion_http_postgres.py"
ADR = ROOT / "docs/adr/0091-accepted-feed-item-normalization-and-source-brief-ingestion.md"
CONTRACT = ROOT / "docs/contracts/source-brief-ingestion-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/source-brief-ingestion-ci.yml"

REQUIRED = (
    STAGE,
    SERVICE,
    ROUTER,
    MODELS,
    PIPELINE,
    MAIN,
    MEMORY_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)


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


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


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


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing Source Brief ingestion files: {missing}")

    stage = STAGE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    models = MODELS.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "source-brief-ingestion-slice55":
        fail("Source Brief ingestion contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Source Brief ingestion contract is not accepted")
    if contract.get("api", {}).get("minimum_version") != "0.22.0":
        fail("Source Brief ingestion API version drifted")
    if contract.get("normalization", {}).get("raw_evidence_read") is not False:
        fail("Source Brief normalization cannot read raw evidence")
    if contract.get("output", {}).get("automatic_case_creation") is not False:
        fail("Source Brief ingestion cannot create Cases automatically")
    if contract.get("output", {}).get("automatic_publication") is not False:
        fail("Source Brief ingestion cannot publish automatically")

    if 'PROPOSAL = "PROPOSAL"' in models:
        fail("Slice 55 must reuse NORMALIZED_ARTIFACT, not add Proposal input")
    if "InMemoryIngestionWorkerRuntimeRegistry()" not in pipeline:
        fail("general production ingestion worker registry must remain empty")

    stage_classes = class_map(stage)
    for name in (
        "NormalizedFeedItemMetadata",
        "SourceBriefStageProcessor",
    ):
        if name not in stage_classes:
            fail(f"Source Brief stage class missing: {name}")
    metadata_fields = fields(stage_classes["NormalizedFeedItemMetadata"])
    if metadata_fields != (
        "parent_feed_item_proposal_id",
        "review_decision_id",
        "source_artifact_id",
        "feed_content_hash",
        "feed_storage_ref",
        "feed_format",
        "feed_title",
        "publisher_or_issuer",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "summary_text",
    ):
        fail(f"normalized feed item metadata fields drifted: {metadata_fields}")
    for fragment in (
        'NORMALIZED_SCHEMA_REF = "kefe.normalized-feed-item"',
        'PIPELINE_CODE = "FEED_ITEM_SOURCE_BRIEF"',
        'STAGE_CODE = "BUILD_SOURCE_BRIEF"',
        'SOURCE_BRIEF_KIND = "SOURCE_BRIEF"',
        'SOURCE_BRIEF_RISK_CODE = "UNREVIEWED_SOURCE_BRIEF"',
        "canonical_normalized_content_hash(metadata.as_mapping())",
        "run.input_artifact_kind is not InputArtifactKind.NORMALIZED_ARTIFACT",
        "self._knowledge.get_normalized_artifact(run.input_artifact_id)",
        "self._knowledge.get_source_artifact(metadata.source_artifact_id)",
        "ProposalDraft(",
    ):
        if fragment not in stage:
            fail(f"Source Brief stage invariant missing: {fragment}")

    service_classes = class_map(service)
    for name in (
        "AcceptedFeedItemNormalizer",
        "SourceBriefIngestionResult",
        "SecuredSourceBriefIngestionService",
    ):
        if name not in service_classes:
            fail(f"Source Brief Admin class missing: {name}")
    build_source = ast.get_source_segment(
        service,
        method(service_classes["SecuredSourceBriefIngestionService"], "build"),
    ) or ""
    ordered = (
        "self._feed_items.detail(",
        "materialize_accepted_proposal(",
        "get_normalized_artifact(",
        "self._ingestion.start_run(",
        "self._execute(run)",
    )
    positions = tuple(build_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
        fail("Source Brief admission execution order drifted")
    for fragment in (
        "ProposalReviewDecisionKind.ACCEPTED",
        "uuid5(",
        "ArtifactKind.EXTERNAL_EVIDENCE",
        "canonical_normalized_content_hash(mapping)",
        "InputArtifactKind.NORMALIZED_ARTIFACT",
        "self._repository.complete_successful_stage(execution, (proposal,))",
        "self._ingestion.mark_succeeded(current.id)",
        "self._recover(",
        "repository.find_materialization",
    ):
        search = service.replace("self._repository", "repository")
        if fragment not in search:
            fail(f"Source Brief service invariant missing: {fragment}")

    forbidden = (
        "RawSourceEvidenceReader",
        "RawSourceEvidenceStore",
        "read_owned_copy",
        "read_exact(",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "openai",
        "materialize_accepted_proposal(brief",
        "create_case",
        "project(",
        "publish(",
        "while True",
        "time.sleep",
    )
    combined_runtime = (stage + service + router).lower()
    for fragment in forbidden:
        if fragment.lower() in combined_runtime:
            fail(f"forbidden authority leaked into Source Brief ingestion: {fragment}")

    router_classes = class_map(router)
    response = router_classes.get("SourceBriefIngestionResponse")
    if response is None or fields(response) != (
        "normalized_artifact_id",
        "run_id",
        "source_brief_proposal_id",
        "run_state",
        "proposal_review_state",
    ):
        fail("Source Brief response fields drifted")
    if '@router.post(' not in router:
        fail("Source Brief Admin command must be POST")
    if '"/feed-items/{proposal_id}/source-brief"' not in router:
        fail("Source Brief Admin path drifted")
    if "WritePrincipalDep" not in router:
        fail("Source Brief Admin command must require CSRF write principal")
    for mutation in ("@router.put", "@router.patch", "@router.delete"):
        if mutation in router:
            fail(f"unexpected Source Brief mutation route: {mutation}")

    if "if _api_at_least(settings.api_version, 0, 22):" not in main_source:
        fail("Source Brief router must be API 0.22 gated")
    if "app.include_router(admin_source_brief_ingestion_router)" not in main_source:
        fail("Source Brief router is not composed")

    for test_name in (
        "test_source_brief_command_is_022_only_authorized_and_idempotent",
        "test_postgres_source_brief_command_is_durable_and_idempotent",
    ):
        if test_name not in tests:
            fail(f"Source Brief test evidence missing: {test_name}")
    for phrase in (
        "NORMALIZED_ARTIFACT",
        "deterministic stage and Proposal identities",
        "requires a second human review",
        "Raw evidence bytes",
        "API 0.22",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")
    for phrase in (
        "Source Brief ingestion architecture and OpenAPI fitness",
        "Source Brief ingestion memory HTTP",
        "Source Brief ingestion PostgreSQL HTTP",
        "Parent Admin feed item review architecture fitness",
        "Parent ingestion orchestration contract",
    ):
        if phrase not in workflow:
            fail(f"Source Brief CI step missing: {phrase}")

    old = _openapi("0.21.0")
    new = _openapi("0.22.0")
    path = contract["api"]["path"]
    if path in old.get("paths", {}):
        fail("Source Brief path leaked into API 0.21")
    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})
    if set(new_paths) - set(old_paths) != {path}:
        fail("API 0.22 path additions drifted")
    for existing_path, definition in old_paths.items():
        if new_paths.get(existing_path) != definition:
            fail(f"API 0.22 changed existing path: {existing_path}")
    if set(new_paths[path]) != {"post"}:
        fail("Source Brief API path must be POST-only")
    operation = new_paths[path]["post"]
    if "requestBody" in operation:
        fail("Source Brief Admin command cannot accept a request body")
    parameters = {item["name"] for item in operation.get("parameters", [])}
    if parameters != {"proposal_id", "X-KEFE-CSRF"}:
        fail(f"Source Brief API parameters drifted: {sorted(parameters)}")

    old_schemas = old.get("components", {}).get("schemas", {})
    new_schemas = new.get("components", {}).get("schemas", {})
    added_schemas = set(new_schemas) - set(old_schemas)
    if added_schemas != {"SourceBriefIngestionResponse"}:
        fail(f"API 0.22 schema additions drifted: {sorted(added_schemas)}")
    for name, definition in old_schemas.items():
        if new_schemas.get(name) != definition:
            fail(f"API 0.22 changed existing schema: {name}")
    response_fields = set(
        new_schemas["SourceBriefIngestionResponse"].get("properties", {})
    )
    if response_fields != set(contract["response_fields"]):
        fail(f"Source Brief response OpenAPI fields drifted: {sorted(response_fields)}")
    forbidden_fields = {
        "payload",
        "raw_body",
        "raw_bytes",
        "evidence_body",
        "backend_object_key",
        "credential",
    }
    if response_fields & forbidden_fields:
        fail("Source Brief response leaks forbidden fields")

    print("Source Brief ingestion contract and OpenAPI: PASS")


if __name__ == "__main__":
    main()

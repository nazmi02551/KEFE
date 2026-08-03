from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
MATERIALIZER = (
    API
    / "src/kefe_api/modules/ingestion_orchestration/knowledge_materializer.py"
)
SERVICE = API / "src/kefe_api/modules/ingestion_orchestration/service.py"
MEMORY_TEST = API / "tests/test_feed_item_normalization_materialization.py"
POSTGRES_TEST = (
    API / "tests/test_feed_item_normalization_materialization_postgres.py"
)
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
ADR = (
    ROOT
    / "docs/adr/0090-human-reviewed-feed-item-normalization-materialization.md"
)
CONTRACT = ROOT / "docs/contracts/feed-item-normalization-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/feed-item-normalization-ci.yml"

REQUIRED = (
    MATERIALIZER,
    SERVICE,
    MEMORY_TEST,
    POSTGRES_TEST,
    PIPELINE,
    MAIN,
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


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing feed item normalization files: {missing}")

    materializer_source = MATERIALIZER.read_text(encoding="utf-8")
    service_source = SERVICE.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "feed-item-normalization-slice54":
        fail("feed item normalization contract identity drifted")
    if contract.get("status") != "accepted":
        fail("feed item normalization contract is not accepted")

    proposal = contract.get("proposal", {})
    if proposal.get("kind") != "FEED_ITEM":
        fail("feed item proposal kind drifted")
    if proposal.get("payload_schema_ref") != "kefe.feed-item":
        fail("feed item payload schema drifted")
    if proposal.get("payload_schema_version") != "1.0.0":
        fail("feed item payload schema version drifted")
    if proposal.get("risk_code") != "UNREVIEWED_EXTERNAL_FEED_ITEM":
        fail("feed item risk code drifted")
    if proposal.get("ai_execution_ref_allowed") is not False:
        fail("feed item normalization cannot accept AI execution references")
    if proposal.get("exact_payload_keys") != [
        "feed_content_hash",
        "feed_format",
        "feed_storage_ref",
        "feed_title",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "source_artifact_id",
        "summary_text",
    ]:
        fail("feed item exact payload key set drifted")

    target = contract.get("target", {})
    if target.get("target_kind") != "NORMALIZED_ARTIFACT":
        fail("feed item target kind drifted")
    if target.get("artifact_kind") != "EXTERNAL_EVIDENCE":
        fail("feed item artifact kind drifted")
    if target.get("generated_interpretation") is not False:
        fail("feed item materialization cannot generate interpretation")
    if target.get("semantic_classification") is not False:
        fail("feed item materialization cannot classify semantics")

    idempotency = contract.get("idempotency", {})
    for name in (
        "deterministic_target_id",
        "exact_existing_target_reused",
        "conflicting_existing_target_rejected",
        "repository_race_reread",
        "partial_success_retry_safe",
    ):
        if idempotency.get(name) is not True:
            fail(f"feed item idempotency invariant drifted: {name}")

    classes = class_map(materializer_source)
    materializer = classes.get("KnowledgeProposalMaterializer")
    if materializer is None:
        fail("KnowledgeProposalMaterializer is missing")
    materialize_source = ast.get_source_segment(
        materializer_source,
        method(materializer, "materialize"),
    ) or ""
    feed_source = ast.get_source_segment(
        materializer_source,
        method(materializer, "_feed_item"),
    ) or ""
    safe_add_source = ast.get_source_segment(
        materializer_source,
        method(materializer, "_safe_add_exact_normalized"),
    ) or ""

    materialize_order = (
        materialize_source.find("kind == _FEED_ITEM_KIND"),
        materialize_source.find(
            "self._target_id(proposal.id, _NORMALIZED_ARTIFACT_KIND)"
        ),
        materialize_source.find("self._feed_item(proposal, review, target_id)"),
        materialize_source.find("return _NORMALIZED_ARTIFACT_KIND, target_id"),
    )
    if any(position < 0 for position in materialize_order) or materialize_order != tuple(
        sorted(materialize_order)
    ):
        fail("feed item proposal routing order drifted")

    for fragment in (
        "review.proposal_id != proposal.id",
        "review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "proposal.payload_schema_ref != _FEED_ITEM_SCHEMA_REF",
        "proposal.payload_schema_version != _FEED_ITEM_SCHEMA_VERSION",
        "proposal.risk_code != _FEED_ITEM_RISK_CODE",
        "proposal.ai_execution_ref is not None",
        "frozenset(payload) != _FEED_ITEM_PAYLOAD_KEYS",
        "self._knowledge.get_source_artifact(source_id)",
        "canonical_storage_ref(feed_content_hash)",
        "source.content_hash != feed_content_hash",
        "source.raw_storage_ref != feed_storage_ref",
        "proposal.provenance_ref != feed_storage_ref",
        "content_hash = f\"sha256:{stable_payload_hash(canonical_content)}\"",
        "artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE",
        "normalized_at=review.decided_at",
        "language_code=source.language_code",
        "jurisdiction_code=source.jurisdiction_code",
        "self._safe_add_exact_normalized(item)",
    ):
        if fragment not in feed_source:
            fail(f"feed item materialization guard missing: {fragment}")

    for forbidden in (
        "add_claim(",
        "add_argument(",
        "create_case",
        "publish(",
        "projection",
        "requests",
        "httpx",
        "socket",
        "openai",
        "raw_xml",
        "object_key",
    ):
        if forbidden in feed_source:
            fail(f"forbidden behavior leaked into feed item handler: {forbidden}")

    for fragment in (
        "existing = self._knowledge.get_normalized_artifact(item.id)",
        "if existing != item:",
        "conflicting normalized artifact already exists",
        "self._knowledge.add_normalized_artifact(item)",
        "if existing == item:",
    ):
        if fragment not in safe_add_source:
            fail(f"exact normalized artifact retry guard missing: {fragment}")

    if "ProposalReviewDecisionKind.ACCEPTED" not in service_source:
        fail("orchestration accepted-review gate was removed")
    if "materialize_accepted_proposal(" in pipeline or (
        "materialize_accepted_proposal(" in main_source
    ):
        fail("production composition cannot auto-materialize feed items")
    composition = contract.get("composition", {})
    if composition != {
        "automatic_materialization_workers_registered": 0,
        "production_feed_providers_registered": 0,
        "production_feed_ingestion_plans_registered": 0,
    }:
        fail("feed item normalization production boundary drifted")

    for test_name in (
        "test_accepted_feed_item_materializes_deterministic_normalized_artifact",
        "test_missing_or_rejected_review_cannot_materialize_feed_item",
        "test_materializer_defends_against_review_and_source_authority_drift",
        "test_feed_item_payload_validation_fails_closed",
        "test_partial_success_retry_reuses_exact_target_and_rejects_conflict",
        "test_postgres_feed_item_partial_retry_and_conflict_are_deterministic",
    ):
        if test_name not in tests:
            fail(f"feed item normalization test evidence missing: {test_name}")

    for phrase in (
        "ACCEPTED review remains mandatory",
        "Persisted SourceArtifact is authoritative",
        "Deterministic immutable target",
        "Retry and conflict semantics",
        "does not activate a provider",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "Feed item normalization architecture fitness",
        "Feed item normalization memory behavior",
        "Feed item normalization PostgreSQL behavior",
        "Parent feed item extraction architecture fitness",
        "Parent ingestion orchestration architecture fitness",
        "check_feed_item_normalization_contract.py",
    ):
        if phrase not in workflow:
            fail(f"feed item normalization CI step missing: {phrase}")

    print("feed item normalization contract: PASS")


if __name__ == "__main__":
    main()

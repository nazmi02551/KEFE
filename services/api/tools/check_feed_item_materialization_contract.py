from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
MATERIALIZER = (
    API
    / "src/kefe_api/modules/ingestion_orchestration/feed_item_materializer.py"
)
KNOWLEDGE_MATERIALIZER = (
    API
    / "src/kefe_api/modules/ingestion_orchestration/knowledge_materializer.py"
)
SERVICE = API / "src/kefe_api/modules/ingestion_orchestration/service.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MEMORY_TEST = API / "tests/test_feed_item_materializer.py"
POSTGRES_TEST = API / "tests/test_feed_item_materializer_postgres.py"
ADR = (
    ROOT
    / "docs/adr/0092-human-approved-feed-item-materialization-into-immutable-normalized-artifact.md"
)
CONTRACT = ROOT / "docs/contracts/feed-item-materialization-slice56.v1.json"
WORKFLOW = ROOT / ".github/workflows/feed-item-materialization-ci.yml"

REQUIRED = (
    MATERIALIZER,
    KNOWLEDGE_MATERIALIZER,
    SERVICE,
    PIPELINE,
    MEMORY_TEST,
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


def segment(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing feed item materialization files: {missing}")

    materializer = MATERIALIZER.read_text(encoding="utf-8")
    knowledge_materializer = KNOWLEDGE_MATERIALIZER.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "feed-item-materialization-slice56":
        fail("feed item materialization contract identity drifted")
    if contract.get("status") != "accepted":
        fail("feed item materialization contract is not accepted")
    input_contract = contract.get("input", {})
    if input_contract.get("proposal_kind") != "FEED_ITEM":
        fail("feed item proposal kind drifted")
    if input_contract.get("payload_schema_ref") != "kefe.feed-item":
        fail("feed item payload schema reference drifted")
    if input_contract.get("payload_schema_version") != "1.0.0":
        fail("feed item payload schema version drifted")
    if input_contract.get("review_decision") != "ACCEPTED":
        fail("feed item materialization must require ACCEPTED review")
    if input_contract.get("exact_payload_fields") != [
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
    ]:
        fail("feed item materialization payload fields drifted")

    target = contract.get("target", {})
    if target.get("target_kind") != "NORMALIZED_ARTIFACT":
        fail("feed item target kind drifted")
    if target.get("artifact_kind") != "EXTERNAL_EVIDENCE":
        fail("feed item artifact kind drifted")
    for name in (
        "deterministic_uuid_v5",
        "idempotent_exact_replay",
    ):
        if target.get(name) is not True:
            fail(f"feed item target invariant drifted: {name}")
    metadata = contract.get("metadata", {})
    for name in (
        "raw_feed_bytes",
        "raw_storage_ref_copied",
        "credential_material",
        "backend_object_key",
    ):
        if metadata.get(name) is not False:
            fail(f"normalized feed item metadata boundary drifted: {name}")

    classes = class_map(materializer)
    item_class = classes.get("FeedItemProposalMaterializer")
    if item_class is None:
        fail("FeedItemProposalMaterializer is missing")
    materialize = method(item_class, "materialize")
    materialize_source = segment(materializer, materialize)
    ordered = (
        "review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "self._require_proposal_identity(proposal)",
        "frozenset(payload) != _PAYLOAD_FIELDS",
        "self._knowledge.get_source_artifact(source_id)",
        "self._require_source_lineage(",
        "canonical_text =",
        "target_id = uuid5(",
        "artifact = NormalizedArtifact(",
        "self._add_exact(artifact)",
        "return TARGET_KIND, target_id",
    )
    positions = tuple(materialize_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(
        sorted(positions)
    ):
        fail("feed item materialization validation/assembly order drifted")
    for fragment in (
        "artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE",
        "normalized_at=review.decided_at",
        "language_code=source.language_code",
        "jurisdiction_code=source.jurisdiction_code",
        'f"sha256:{sha256(canonical_text.encode(\'utf-8\')).hexdigest()}"',
        '"proposal_id": str(proposal.id)',
        '"review_id": str(review.id)',
        '"reviewer_ref": reviewer_ref',
        '"provenance_ref": provenance_ref',
    ):
        if fragment not in materialize_source:
            fail(f"normalized feed item assembly invariant missing: {fragment}")
    metadata_source = materialize_source.split("media_metadata={", 1)[-1].split(
        "},", 1
    )[0]
    for forbidden in (
        '"feed_storage_ref"',
        "source.raw_storage_ref",
        "proposal.provenance_ref",
    ):
        if forbidden in metadata_source:
            fail(f"raw evidence reference leaked into normalized metadata: {forbidden}")

    lineage_source = segment(materializer, method(item_class, "_require_source_lineage"))
    for fragment in (
        "source.content_hash != feed_content_hash",
        "source.raw_storage_ref != feed_storage_ref",
        "canonical_storage_ref(source.content_hash) != source.raw_storage_ref",
    ):
        if fragment not in lineage_source:
            fail(f"feed item source lineage guard missing: {fragment}")
    provenance_source = segment(materializer, method(item_class, "_provenance"))
    if 'value = f"proposal:{proposal.id};review:{review.id}"' not in (
        provenance_source
    ):
        fail("feed item provenance must derive only from proposal and review IDs")
    if "proposal.provenance_ref" in provenance_source:
        fail("raw proposal provenance cannot flow into normalized metadata")
    add_source = segment(materializer, method(item_class, "_add_exact"))
    for fragment in (
        "existing != artifact",
        "self._knowledge.add_normalized_artifact(artifact)",
        "existing == artifact",
    ):
        if fragment not in add_source:
            fail(f"feed item exact replay guard missing: {fragment}")

    if '"FEED_ITEM"' in knowledge_materializer:
        fail("Claim/Argument KnowledgeProposalMaterializer cannot handle FEED_ITEM")
    if "review.decision is not ProposalReviewDecisionKind.ACCEPTED" not in (
        materialize_source
    ):
        fail("feed item materializer lacks local ACCEPTED review guard")
    for phrase in (
        "review is None or review.decision is not ProposalReviewDecisionKind.ACCEPTED",
        "proposal must have an ACCEPTED review decision",
    ):
        if phrase not in service:
            fail(f"orchestration human-review gate missing: {phrase}")

    for forbidden in (
        "review_proposal(",
        "add_claim(",
        "materialize_accepted_proposal(",
        "project(",
        "publish(",
        "create_case",
        "SecretAccess",
        "use_bytes",
        "requests",
        "httpx",
        "socket",
        "raw_storage_ref=",
    ):
        if forbidden in materializer:
            fail(f"forbidden authority leaked into feed item materializer: {forbidden}")

    for phrase in (
        "FeedItemProposalMaterializer(",
        "feed_item_proposal_materializer",
    ):
        if phrase not in pipeline:
            fail(f"production feed item materializer composition missing: {phrase}")
    if "materialize_accepted_proposal(" in pipeline:
        fail("production composition must perform zero automatic materializations")
    composition = contract.get("composition", {})
    if composition.get("production_automatic_materializations") != 0:
        fail("production automatic feed item materializations must remain zero")

    for test_name in (
        "test_accepted_feed_item_materializes_deterministic_normalized_artifact",
        "test_unreviewed_rejected_and_changes_requested_proposals_cannot_materialize",
        "test_schema_payload_and_source_lineage_drift_fail_closed",
        "test_noncanonical_item_fields_and_conflicting_target_fail_closed",
        "test_postgres_accepted_feed_item_materialization_is_idempotent",
    ):
        if test_name not in tests:
            fail(f"feed item materialization test evidence missing: {test_name}")

    for phrase in (
        "dedicated `FeedItemProposalMaterializer`",
        "terminal `ACCEPTED` review",
        "Raw feed bytes",
        "KnowledgeProposalMaterializer` remains unchanged",
        "Human review remains mandatory",
    ):
        if phrase not in adr:
            fail(f"ADR-0092 decision text missing: {phrase}")

    for phrase in (
        "Feed item materialization architecture fitness",
        "Feed item materialization behavior",
        "Feed item materialization PostgreSQL",
        "Parent ingestion orchestration architecture fitness",
        "Parent feed item extraction architecture fitness",
        "check_feed_item_materialization_contract.py",
    ):
        if phrase not in workflow:
            fail(f"feed item materialization CI step missing: {phrase}")

    print("feed item materialization contract: PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
EVIDENCE = API / "src/kefe_api/modules/knowledge/source_evidence.py"
DURABLE = API / "src/kefe_api/modules/knowledge/source_evidence_backend.py"
EXTRACTION = (
    API
    / "src/kefe_api/modules/ingestion_orchestration/feed_item_extraction.py"
)
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
READ_TEST = API / "tests/test_source_evidence_reading.py"
STAGE_TEST = API / "tests/test_feed_item_extraction.py"
ADR = (
    ROOT
    / "docs/adr/0089-immutable-feed-evidence-reading-and-bounded-item-extraction.md"
)
CONTRACT = ROOT / "docs/contracts/feed-item-extraction-slice53.v1.json"
WORKFLOW = ROOT / ".github/workflows/feed-item-extraction-ci.yml"

REQUIRED = (
    EVIDENCE,
    DURABLE,
    EXTRACTION,
    PIPELINE,
    MAIN,
    READ_TEST,
    STAGE_TEST,
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


def arguments(node: ast.FunctionDef) -> tuple[str, ...]:
    return tuple(
        argument.arg
        for argument in (*node.args.args, *node.args.kwonlyargs)
    )


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing feed item extraction files: {missing}")

    evidence = EVIDENCE.read_text(encoding="utf-8")
    durable = DURABLE.read_text(encoding="utf-8")
    extraction = EXTRACTION.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = READ_TEST.read_text(encoding="utf-8") + STAGE_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "feed-item-extraction-slice53":
        fail("feed item extraction contract identity drifted")
    if contract.get("status") != "accepted":
        fail("feed item extraction contract is not accepted")
    evidence_read_contract = contract.get("evidence_read", {})
    if evidence_read_contract.get("owned_body_copy") is not True:
        fail("evidence reads must return an owned body copy")
    if evidence_read_contract.get("sha256_recomputed") is not True:
        fail("evidence reads must recompute SHA-256")
    if evidence_read_contract.get("backend_object_key_exposed") is not False:
        fail("evidence reader cannot expose backend object keys")
    if evidence_read_contract.get("network_fallback") is not False:
        fail("evidence reader network fallback is forbidden")
    if evidence_read_contract.get("preview_fallback") is not False:
        fail("evidence reader preview fallback is forbidden")

    evidence_classes = class_map(evidence)
    read_model = evidence_classes.get("RawSourceEvidenceRead")
    if read_model is None or fields(read_model) != (
        "content_hash",
        "storage_ref",
        "body",
        "media_type",
        "byte_length",
    ):
        fail("RawSourceEvidenceRead fields drifted")
    reader = evidence_classes.get("RawSourceEvidenceReader")
    if reader is None or "Protocol" not in {
        ast.unparse(base) for base in reader.bases
    }:
        fail("RawSourceEvidenceReader must be a Protocol")
    read_method = method(reader, "read")
    if arguments(read_method) != (
        "self",
        "storage_ref",
        "expected_content_hash",
    ):
        fail("RawSourceEvidenceReader.read signature drifted")
    for fragment in (
        "content_hash_from_storage_ref(storage_ref)",
        "canonical_content_hash(owned_body)",
        "RAW_EVIDENCE_REFERENCE_HASH_MISMATCH",
        "RAW_EVIDENCE_READ_DIGEST_MISMATCH",
        "RAW_EVIDENCE_READER_UNAVAILABLE",
        "body=<redacted:",
    ):
        if fragment not in evidence and fragment not in durable:
            fail(f"evidence read invariant missing: {fragment}")

    durable_classes = class_map(durable)
    durable_store = durable_classes.get("DurableRawSourceEvidenceStore")
    if durable_store is None or "read" not in {
        child.name
        for child in durable_store.body
        if isinstance(child, ast.FunctionDef)
    }:
        fail("durable raw evidence store must implement read")
    for forbidden in (
        "external_locator",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "preview",
    ):
        if forbidden in durable.lower():
            fail(f"forbidden fallback leaked into durable evidence read: {forbidden}")

    stage_contract = contract.get("stage", {})
    expected_stage = {
        "pipeline_code": "RSS_ATOM_FEED_ITEM_EXTRACTION",
        "pipeline_version": "1.0.0",
        "stage_code": "EXTRACT_FEED_ITEMS",
        "stage_version": "1.0.0",
        "executor_kind": "DETERMINISTIC",
        "input_artifact_kind": "SOURCE_ARTIFACT",
        "strict_source_artifact_match": True,
        "strict_input_hash_match": True,
        "strict_rss_atom_validation_before_extraction": True,
        "second_permissive_parser": False,
        "proposal_kind": "FEED_ITEM",
        "payload_schema_ref": "kefe.feed-item",
        "payload_schema_version": "1.0.0",
        "automatic_review": False,
        "automatic_materialization": False,
        "automatic_publication": False,
    }
    if stage_contract != expected_stage:
        fail(f"feed item stage contract drifted: {stage_contract}")

    extraction_classes = class_map(extraction)
    for class_name in (
        "ExtractedFeedItem",
        "ExtractedFeedDocument",
        "FeedItemExtractionStageProcessor",
    ):
        if class_name not in extraction_classes:
            fail(f"feed item extraction class is missing: {class_name}")
    processor = extraction_classes["FeedItemExtractionStageProcessor"]
    process = method(processor, "process")
    process_source = ast.get_source_segment(ast.parse(extraction), process) or ""
    validation_position = process_source.find("definition.parse_response(")
    traversal_position = process_source.find("self._extract_validated_document(")
    proposal_position = process_source.find("ProposalDraft(")
    if not 0 <= validation_position < traversal_position < proposal_position:
        fail("strict validation/extraction/proposal order drifted")
    for fragment in (
        "run.input_artifact_kind is not InputArtifactKind.SOURCE_ARTIFACT",
        "artifact.content_hash != input_hash",
        "canonical_storage_ref(artifact.content_hash)",
        "self._evidence.read(",
        "FEED_ITEM_DUPLICATE_IDENTITY",
        "sorted(document.items, key=lambda candidate: candidate.item_id)",
        "risk_code=RISK_CODE",
    ):
        if fragment not in extraction:
            fail(f"feed item extraction guard missing: {fragment}")

    for forbidden in (
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "add_claim(",
        "create_case",
        "openai",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "BeautifulSoup",
        "lxml",
        "eval(",
        "exec(",
    ):
        if forbidden in extraction:
            fail(f"forbidden behavior leaked into extraction stage: {forbidden}")

    if "InMemoryIngestionWorkerRuntimeRegistry()" not in pipeline:
        fail("production ingestion runtime registry must remain empty")
    if "build_feed_item_extraction_runtime(" in pipeline or (
        "build_feed_item_extraction_runtime(" in main_source
    ):
        fail("production composition must not activate feed item extraction")
    composition = contract.get("composition", {})
    if composition.get("production_runtime_plans_registered") != 0:
        fail("production feed item runtime plan registry must remain empty")
    if composition.get("production_processors_registered") != 0:
        fail("production feed item processor registry must remain empty")

    for test_name in (
        "test_in_memory_read_returns_owned_integrity_verified_record",
        "test_reference_hash_mismatch_rejected_before_object_lookup",
        "test_durable_read_derives_object_key_and_recomputes_digest",
        "test_unconfigured_reader_is_bounded_retryable",
        "test_rss_stage_emits_deterministic_reviewable_proposals",
        "test_atom_stage_extracts_alternate_link_summary_and_content",
        "test_duplicate_identity_and_source_mismatch_fail_closed",
        "test_evidence_retryable_and_reference_integrity_are_mapped",
        "test_full_ingestion_worker_persists_proposals_without_review_or_materialization",
    ):
        if test_name not in tests:
            fail(f"feed item extraction test evidence missing: {test_name}")

    for phrase in (
        "explicit read capability",
        "recompute SHA-256",
        "strict RSS/Atom validator",
        "Human review remains mandatory",
        "runtime registry remains empty",
    ):
        if phrase not in adr:
            fail(f"ADR-0089 decision text missing: {phrase}")

    for phrase in (
        "Feed item extraction architecture fitness",
        "Feed item extraction behavior",
        "Parent raw evidence architecture fitness",
        "Parent ingestion worker architecture fitness",
        "check_feed_item_extraction_contract.py",
    ):
        if phrase not in workflow:
            fail(f"feed item extraction CI step missing: {phrase}")

    print("feed item extraction contract: PASS")


if __name__ == "__main__":
    main()

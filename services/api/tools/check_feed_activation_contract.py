from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
DOMAIN = API / "src/kefe_api/modules/knowledge/feed_activation.py"
POSTGRES = API / "src/kefe_api/infrastructure/postgres_feed_activation.py"
RUNTIME = API / "src/kefe_api/infrastructure/feed_activation_runtime.py"
EVIDENCE = API / "src/kefe_api/modules/knowledge/source_evidence.py"
EVIDENCE_RUNTIME = API / "src/kefe_api/infrastructure/raw_evidence_runtime.py"
MIGRATION = (
    API / "migrations/versions/20260803_0026_feed_pipeline_activation.py"
)
MEMORY_TEST = API / "tests/test_feed_activation.py"
POSTGRES_TEST = API / "tests/test_feed_activation_postgres.py"
RUNTIME_TEST = API / "tests/test_feed_activation_runtime.py"
ADR = (
    ROOT
    / "docs/adr/0090-feed-pipeline-activation-governance-and-read-only-preflight.md"
)
CONTRACT = ROOT / "docs/contracts/feed-pipeline-activation-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/feed-activation-governance-ci.yml"

REQUIRED = (
    DOMAIN,
    POSTGRES,
    RUNTIME,
    EVIDENCE,
    EVIDENCE_RUNTIME,
    MIGRATION,
    MEMORY_TEST,
    POSTGRES_TEST,
    RUNTIME_TEST,
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
        item.target.id
        for item in node.body
        if isinstance(item, ast.AnnAssign)
        and isinstance(item.target, ast.Name)
    )


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing feed activation governance files: {missing}")

    domain = DOMAIN.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")
    evidence_runtime = EVIDENCE_RUNTIME.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    tests = (
        MEMORY_TEST.read_text(encoding="utf-8")
        + POSTGRES_TEST.read_text(encoding="utf-8")
        + RUNTIME_TEST.read_text(encoding="utf-8")
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "feed-pipeline-activation-slice54":
        fail("feed activation contract identity drifted")
    if contract.get("status") != "accepted":
        fail("feed activation contract is not accepted")
    definition_contract = contract.get("definition", {})
    if definition_contract.get("configuration_immutable") is not True:
        fail("feed activation configuration must remain immutable")
    if definition_contract.get("semantic_change_requires_new_version") is not True:
        fail("feed semantic changes must require a new version")
    lifecycle_contract = contract.get("lifecycle", {})
    if lifecycle_contract.get("states") != [
        "DRAFT",
        "PAUSED",
        "ENABLED",
        "RETIRED",
    ]:
        fail("feed activation lifecycle states drifted")
    if lifecycle_contract.get("retired_terminal") is not True:
        fail("retired feed definitions must remain terminal")

    classes = class_map(domain)
    lifecycle = classes.get("FeedPipelineLifecycle")
    if lifecycle is None:
        fail("FeedPipelineLifecycle is missing")
    lifecycle_values = {
        child.targets[0].id: child.value.value
        for child in lifecycle.body
        if isinstance(child, ast.Assign)
        and isinstance(child.targets[0], ast.Name)
        and isinstance(child.value, ast.Constant)
    }
    if lifecycle_values != {
        "DRAFT": "DRAFT",
        "PAUSED": "PAUSED",
        "ENABLED": "ENABLED",
        "RETIRED": "RETIRED",
    }:
        fail(f"FeedPipelineLifecycle drifted: {lifecycle_values}")

    definition = classes.get("FeedPipelineDefinition")
    expected_fields = (
        "feed_code",
        "adapter_code",
        "external_locator",
        "adoption_configuration_hash",
        "parser_configuration_hash",
        "extraction_pipeline_code",
        "extraction_pipeline_version",
        "acquisition_configuration_hash",
        "interval_seconds",
        "max_dispatch_attempts",
        "evidence_capability_ref",
        "lifecycle_state",
        "dependency_fingerprint",
        "verified_at",
        "created_at",
        "updated_at",
    )
    if definition is None or fields(definition) != expected_fields:
        fail("FeedPipelineDefinition fields drifted")
    for fragment in (
        "def immutable_configuration(self)",
        "feed pipeline lifecycle transition is invalid",
        "enabling requires a dependency fingerprint",
        "external_locator=<redacted>",
        "evidence_capability_ref=<redacted>",
    ):
        if fragment not in domain:
            fail(f"feed definition invariant missing: {fragment}")

    result = classes.get("FeedActivationResult")
    if result is None or fields(result) != (
        "outcome",
        "feed_code",
        "lifecycle_state",
        "reason_code",
        "dependency_fingerprint",
        "verified_at",
    ):
        fail("FeedActivationResult allowlist drifted")

    service = classes.get("FeedActivationService")
    if service is None:
        fail("FeedActivationService is missing")
    verify = method(service, "_verify_dependencies")
    verify_source = ast.get_source_segment(domain, verify) or ""
    for fragment in (
        "ProviderCredentialMode.PUBLIC",
        "ProviderCapabilityLifecycle.ENABLED",
        "adoption_configuration_hash(adoption)",
        "self._auth_profiles.get(definition.adapter_code)",
        'getattr(self._evidence_store, "configured", False)',
        "self._public_http_factory.create(",
        "self._ingestion_runtime.get_plan(",
        "ExecutorKind.DETERMINISTIC",
        "FEED_ACTIVATION_DEPENDENCY_DRIFT",
    ):
        if fragment not in verify_source:
            fail(f"feed activation preflight guard missing: {fragment}")
    for forbidden in (
        ".execute(",
        ".seal(",
        ".read(",
        "create_schedule(",
        "dispatch_due(",
        "start_run(",
        "add_proposals(",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "resolve(",
        "socket",
        "requests",
        "httpx",
        "urllib.request",
        "while True",
        "time.sleep",
    ):
        if forbidden in verify_source:
            fail(f"preflight side effect leaked: {forbidden}")

    preflight_contract = contract.get("preflight", {})
    for key in (
        "network_request",
        "dns_resolution",
        "socket_open",
        "secret_resolution",
        "evidence_write",
        "schedule_create",
        "dispatch_create",
        "ingestion_run_create",
        "proposal_create",
    ):
        if preflight_contract.get(key) is not False:
            fail(f"preflight side effect contract drifted: {key}")
    if preflight_contract.get("read_only") is not True:
        fail("preflight must remain read-only")

    for fragment in (
        'revision = "20260803_0026"',
        'down_revision = "20260803_0025"',
        "CREATE TABLE knowledge.feed_pipeline_definition",
        "max_dispatch_attempts BETWEEN 1 AND 10",
        "dependency_fingerprint IS NULL AND verified_at IS NULL",
        "cannot downgrade while feed pipeline definitions exist",
    ):
        if fragment not in migration:
            fail(f"feed activation migration invariant missing: {fragment}")
    if "FOR UPDATE" not in postgres:
        fail("PostgreSQL feed activation lifecycle must use FOR UPDATE")
    if "ON CONFLICT (feed_code) DO NOTHING" not in postgres:
        fail("PostgreSQL feed activation create-or-get is missing")

    for fragment in (
        "InMemoryFeedPipelineDefinitionRepository()",
        "PostgresFeedPipelineDefinitionRepository(",
        "InMemoryFeedParserProfileRegistry()",
        "FeedActivationService(",
    ):
        if fragment not in runtime:
            fail(f"feed activation runtime composition missing: {fragment}")
    if "StrictRssAtomParseProfile(" in runtime:
        fail("production feed activation parser registry must remain empty")

    for fragment in (
        "def configured(self) -> bool:",
        "def capability_ref(self)",
        "ConfiguredRawSourceEvidenceStore",
        "capability_ref=profile.capability_evidence_ref",
    ):
        if fragment not in evidence and fragment not in evidence_runtime:
            fail(f"raw evidence activation capability missing: {fragment}")

    composition = contract.get("composition", {})
    if composition.get("production_feed_definitions_registered") != 0:
        fail("production feed definition registry must remain empty")
    if composition.get("production_enabled_feeds") != 0:
        fail("production enabled feed count must remain zero")
    if composition.get("production_schedules_created") != 0:
        fail("production schedule count must remain zero")

    for test_name in (
        "test_enable_records_exact_fingerprint_without_side_effects",
        "test_configuration_is_immutable_and_lifecycle_is_terminal",
        "test_preflight_dependencies_fail_closed_without_mutation",
        "test_adoption_hash_and_evidence_capability_mismatch_fail_closed",
        "test_runtime_dependency_drift_is_detected_after_pause",
        "test_postgres_create_or_get_is_immutable_and_transitions_are_durable",
        "test_postgres_concurrent_enable_uses_row_lock_and_exactly_one_transition",
        "test_memory_feed_activation_runtime_starts_empty_and_disabled",
    ):
        if test_name not in tests:
            fail(f"feed activation test evidence missing: {test_name}")

    for phrase in (
        "read-only preflight",
        "performs DNS",
        "Production composition starts with an empty feed-definition repository",
        "Actual scheduler materialization remains a later",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "Feed activation governance architecture fitness",
        "Feed activation governance memory behavior",
        "Feed activation governance PostgreSQL behavior",
        "Verify empty-table downgrade and upgrade",
        "check_feed_activation_contract.py",
    ):
        if phrase not in workflow:
            fail(f"feed activation CI step missing: {phrase}")

    print("feed activation governance contract: PASS")


if __name__ == "__main__":
    main()

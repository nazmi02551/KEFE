from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
MODULE = API / "src/kefe_api/modules/knowledge/rss_atom_subscription.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
TEST = API / "tests/test_rss_atom_subscription.py"
ADR = (
    ROOT
    / "docs/adr/0090-versioned-rss-atom-subscription-manifests-and-dormant-activation-runtime.md"
)
CONTRACT = (
    ROOT
    / "docs/contracts/rss-atom-subscription-activation-slice54.v1.json"
)
WORKFLOW = ROOT / ".github/workflows/rss-atom-subscription-activation-ci.yml"

REQUIRED = (MODULE, PIPELINE, MAIN, TEST, ADR, CONTRACT, WORKFLOW)
MANIFEST_FIELDS = (
    "subscription_code",
    "adapter_code",
    "external_locator",
    "interval_seconds",
    "max_dispatch_attempts",
    "quota_limit",
    "quota_window_seconds",
    "failure_threshold",
    "circuit_open_seconds",
    "permit_ttl_seconds",
    "connect_timeout_ms",
    "read_timeout_ms",
    "total_timeout_ms",
    "max_redirect_hops",
    "terms_evidence_ref",
    "rate_limit_evidence_ref",
    "locale",
    "jurisdiction_code",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.parse(source).body
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


def dataclass_keywords(node: ast.ClassDef) -> dict[str, object]:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if ast.unparse(decorator.func) != "dataclass":
            continue
        return {
            keyword.arg: keyword.value.value
            for keyword in decorator.keywords
            if keyword.arg is not None
            and isinstance(keyword.value, ast.Constant)
        }
    return {}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing RSS/Atom subscription activation files: {missing}")

    module = MODULE.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "rss-atom-subscription-activation-slice54":
        fail("RSS/Atom subscription activation contract identity drifted")
    if contract.get("status") != "accepted":
        fail("RSS/Atom subscription activation contract is not accepted")
    manifest_contract = contract.get("manifest", {})
    expected_manifest = {
        "immutable": True,
        "versioned_subscription_code": True,
        "versioned_adapter_code": True,
        "credential_mode": "PUBLIC",
        "secret_ref_allowed": False,
        "locator_scheme": "https",
        "locator_userinfo_allowed": False,
        "locator_fragment_allowed": False,
        "configuration_hash": "sha256-canonical-manifest",
        "parser_profile": "STRICT_RSS_ATOM_SLICE52_DEFAULT",
        "pipeline_code": "RSS_ATOM_FEED_ITEM_EXTRACTION",
        "pipeline_version": "1.0.0",
        "stage_code": "EXTRACT_FEED_ITEMS",
        "stage_version": "1.0.0",
    }
    if manifest_contract != expected_manifest:
        fail(f"RSS/Atom subscription manifest contract drifted: {manifest_contract}")
    activation_contract = contract.get("activation", {})
    if activation_contract.get("order") != [
        "register_public_provider_capability",
        "create_fixed_interval_schedule",
    ]:
        fail("RSS/Atom subscription activation order drifted")
    for key in (
        "explicit_only",
        "idempotent",
        "partial_capability_without_schedule_is_inert",
        "configuration_drift_fails_closed",
    ):
        if activation_contract.get(key) is not True:
            fail(f"RSS/Atom activation invariant must remain true: {key}")
    if activation_contract.get("startup_auto_activation") is not False:
        fail("RSS/Atom startup auto activation must remain disabled")
    production = contract.get("production", {})
    if production != {
        "subscription_manifests_registered": 0,
        "rss_atom_adoption_profiles_registered": 0,
        "rss_atom_public_adapters_registered": 0,
        "feed_ingestion_plans_registered": 0,
        "feed_ingestion_processors_registered": 0,
        "source_schedules_auto_created": 0,
        "concrete_external_feeds": 0,
    }:
        fail(f"RSS/Atom production dormancy contract drifted: {production}")

    classes = class_map(module)
    for class_name in (
        "RssAtomSubscriptionManifest",
        "RssAtomSubscriptionManifestRegistry",
        "RssAtomSubscriptionActivationResult",
        "RssAtomSubscriptionActivationService",
    ):
        if class_name not in classes:
            fail(f"RSS/Atom subscription class missing: {class_name}")
    manifest = classes["RssAtomSubscriptionManifest"]
    if fields(manifest) != MANIFEST_FIELDS:
        fail(f"RSS/Atom subscription manifest fields drifted: {fields(manifest)}")
    if dataclass_keywords(manifest) != {"frozen": True, "slots": True}:
        fail("RSS/Atom subscription manifest must be frozen and slotted")
    result = classes["RssAtomSubscriptionActivationResult"]
    if fields(result) != (
        "subscription_code",
        "adapter_code",
        "provider_capability",
        "schedule",
    ):
        fail("RSS/Atom activation result fields drifted")
    if dataclass_keywords(result) != {"frozen": True, "slots": True}:
        fail("RSS/Atom activation result must be frozen and slotted")

    for fragment in (
        "require_versioned_adapter_code(self.subscription_code)",
        "require_versioned_adapter_code(self.adapter_code)",
        'if parsed.scheme != "https":',
        "parsed.username is not None or parsed.password is not None",
        "parsed.netloc != rendered_host",
        "_FORBIDDEN_QUERY_NAMES",
        "query_pairs != sorted(query_pairs)",
        "ProviderCredentialMode.PUBLIC",
        "secret_ref=None",
        "RSS_ATOM_SUBSCRIPTION_PARSE_PROFILE = StrictRssAtomParseProfile()",
        "from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (",
        "PIPELINE_CODE,",
        "PIPELINE_VERSION,",
        "STAGE_CODE,",
        "STAGE_VERSION,",
        'dumps(payload, sort_keys=True, separators=(",", ":"))',
        'return f"sha256:{sha256(encoded).hexdigest()}"',
        "shared RSS/Atom adapter policy drift",
        "tuple(sorted({manifest.origin for manifest in manifests}))",
        "EvidenceBackedPublicHttpCaptureAdapterFactory",
        "StrictRssAtomCaptureDefinition(",
        "build_feed_item_extraction_runtime(processor)",
    ):
        if fragment not in module:
            fail(f"RSS/Atom subscription invariant missing: {fragment}")

    activation = method(classes["RssAtomSubscriptionActivationService"], "activate")
    activation_source = ast.get_source_segment(module, activation) or ""
    capability_position = activation_source.find("self._admission.register(")
    schedule_position = activation_source.find("self._scheduler.create_schedule(")
    if not 0 <= capability_position < schedule_position:
        fail("RSS/Atom activation must register capability before schedule")
    for fragment in (
        "credential_mode=ProviderCredentialMode.PUBLIC",
        "secret_ref=None",
        "pipeline_code=PIPELINE_CODE",
        "pipeline_version=PIPELINE_VERSION",
        "configuration_hash=manifest.configuration_hash",
    ):
        if fragment not in activation_source:
            fail(f"RSS/Atom activation guard missing: {fragment}")

    for forbidden in (
        "import requests",
        "import httpx",
        "urllib.request",
        "import socket",
        "import ssl",
        "SecretResolver",
        "ProviderHttpAuth",
        "OwnedSensitiveHttpHeaders",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "add_claim(",
        "create_case",
        "while True",
        "time.sleep",
    ):
        if forbidden in module:
            fail(f"forbidden behavior leaked into subscription module: {forbidden}")

    for fragment in (
        "RssAtomSubscriptionManifestRegistry()",
        "build_rss_atom_provider_adoption_registry(",
        "build_rss_atom_public_capture_registry(",
        "build_rss_atom_ingestion_worker_registry(",
        "RssAtomSubscriptionActivationService(",
    ):
        if fragment not in pipeline:
            fail(f"RSS/Atom dormant composition missing: {fragment}")
    if "RssAtomSubscriptionManifest(" in pipeline:
        fail("production pipeline contains a concrete RSS/Atom subscription")
    if ".activate(" in pipeline:
        fail("production pipeline must not activate RSS/Atom subscriptions")
    for fragment in (
        "app.state.rss_atom_subscription_registry",
        "app.state.rss_atom_subscription_activation_service",
    ):
        if fragment not in main_source:
            fail(f"RSS/Atom application state missing: {fragment}")
    if "RssAtomSubscriptionManifest(" in main_source or (
        ".activate(" in main_source
    ):
        fail("application startup must not create or activate an RSS/Atom subscription")

    for test_name in contract.get("required_tests", ()):
        if test_name not in tests:
            fail(f"RSS/Atom subscription test evidence missing: {test_name}")

    for phrase in (
        "immutable, versioned `RssAtomSubscriptionManifest`",
        "allowed HTTP origins are derived",
        "Activation is explicit",
        "does not call activation",
        "Human review remains mandatory",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "RSS Atom subscription activation architecture fitness",
        "RSS Atom subscription activation behavior",
        "Parent source scheduler architecture fitness",
        "Parent feed item extraction architecture fitness",
        "check_rss_atom_subscription_activation_contract.py",
    ):
        if phrase not in workflow:
            fail(f"RSS/Atom subscription CI step missing: {phrase}")

    print("RSS Atom subscription activation contract: PASS")


if __name__ == "__main__":
    main()

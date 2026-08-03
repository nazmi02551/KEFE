from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
ROUTE = API / "src/kefe_api/modules/knowledge/rss_atom_route.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
TEST = API / "tests/test_rss_atom_route.py"
ADR = (
    ROOT
    / "docs/adr/0090-immutable-rss-atom-route-assembly-and-exact-parser-profile-pinning.md"
)
CONTRACT = ROOT / "docs/contracts/rss-atom-route-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/rss-atom-route-ci.yml"

REQUIRED = (ROUTE, PIPELINE, TEST, ADR, CONTRACT, WORKFLOW)


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


def source_segment(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing RSS/Atom route files: {missing}")

    route = ROUTE.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "rss-atom-route-slice54":
        fail("RSS/Atom route contract identity drifted")
    if contract.get("status") != "accepted":
        fail("RSS/Atom route contract is not accepted")
    exact_pipeline = contract.get("exact_pipeline", {})
    if exact_pipeline != {
        "pipeline_code": "RSS_ATOM_FEED_ITEM_EXTRACTION",
        "pipeline_version": "1.0.0",
        "stage_code": "EXTRACT_FEED_ITEMS",
        "stage_version": "1.0.0",
        "proposal_kind": "FEED_ITEM",
        "payload_schema_ref": "kefe.feed-item",
        "payload_schema_version": "1.0.0",
    }:
        fail("RSS/Atom route exact pipeline drifted")
    assembly = contract.get("assembly", {})
    for name in (
        "shared_parser_profile_identity",
        "shared_evidence_store_for_seal_and_read",
    ):
        if assembly.get(name) is not True:
            fail(f"RSS/Atom route assembly invariant drifted: {name}")
    for name in (
        "arbitrary_pipeline_override",
        "arbitrary_configuration_override",
    ):
        if assembly.get(name) is not False:
            fail(f"RSS/Atom route override must remain disabled: {name}")

    classes = class_map(route)
    for class_name in (
        "ReadableRawSourceEvidenceStore",
        "RssAtomRouteProfile",
        "RssAtomRouteBundle",
        "RssAtomRouteFactory",
        "RssAtomRouteRegistry",
        "InMemoryRssAtomRouteRegistry",
    ):
        if class_name not in classes:
            fail(f"RSS/Atom route class is missing: {class_name}")

    profile = classes["RssAtomRouteProfile"]
    if fields(profile) != (
        "route_code",
        "adapter_code",
        "parser_profile",
        "locale",
        "jurisdiction_code",
    ):
        fail("RssAtomRouteProfile fields drifted")
    profile_source = source_segment(route, profile)
    for fragment in (
        "type(self.parser_profile) is not StrictRssAtomParseProfile",
        "self.parser_profile.immutable_configuration",
        'return f"sha256:{sha256(encoded).hexdigest()}"',
        "pipeline_code=PIPELINE_CODE",
        "pipeline_version=PIPELINE_VERSION",
        "configuration_hash=self.configuration_hash",
    ):
        if fragment not in profile_source:
            fail(f"route profile invariant missing: {fragment}")
    command = method(profile, "acquisition_command")
    command_args = tuple(
        item.arg for item in (*command.args.args, *command.args.kwonlyargs)
    )
    if command_args != ("self", "external_locator"):
        fail("route acquisition command accepts override authority")

    bundle = classes["RssAtomRouteBundle"]
    if fields(bundle) != (
        "profile",
        "capture_definition",
        "public_adapter",
        "extraction_processor",
        "ingestion_registry",
    ):
        fail("RssAtomRouteBundle fields drifted")
    bundle_source = source_segment(route, bundle)
    for fragment in (
        "self.capture_definition.profile is not self.profile.parser_profile",
        'getattr(self.extraction_processor, "_profile", None)',
        "processor is not self.extraction_processor",
        "len(plan.stages) != 1",
    ):
        if fragment not in bundle_source:
            fail(f"route bundle drift guard missing: {fragment}")

    factory = classes["RssAtomRouteFactory"]
    build_source = source_segment(route, method(factory, "build"))
    ordered = (
        "StrictRssAtomCaptureDefinition(",
        "self._capture_factory.create(definition)",
        "FeedItemExtractionStageProcessor(",
        "build_feed_item_extraction_runtime(",
        "return RssAtomRouteBundle(",
    )
    positions = tuple(build_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(
        sorted(positions)
    ):
        fail("RSS/Atom route assembly order drifted")
    if build_source.count("profile=profile.parser_profile") != 2:
        fail("capture and extraction must receive the same parser profile")
    init_source = source_segment(route, method(factory, "__init__"))
    for fragment in (
        'getattr(evidence_store, "seal", None)',
        'getattr(evidence_store, "read", None)',
        "evidence_store=evidence_store",
        "self._evidence_store = evidence_store",
    ):
        if fragment not in init_source:
            fail(f"shared evidence-store assembly missing: {fragment}")

    registry = classes["InMemoryRssAtomRouteRegistry"]
    registry_source = source_segment(route, registry)
    for fragment in (
        "duplicate RSS/Atom route code",
        "duplicate RSS/Atom route adapter code",
        "RSS_ATOM_ROUTE_NOT_REGISTERED",
        "MappingProxyType",
    ):
        if fragment not in registry_source:
            fail(f"route registry invariant missing: {fragment}")

    for forbidden in (
        "SecretAccess",
        "SecretResolver",
        "use_bytes",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "create_case",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "while True",
        "time.sleep",
    ):
        if forbidden in route:
            fail(f"forbidden authority leaked into RSS/Atom route: {forbidden}")

    for phrase in (
        "RssAtomRouteFactory(",
        "InMemoryRssAtomRouteRegistry()",
        "rss_atom_route_factory",
        "rss_atom_route_registry",
    ):
        if phrase not in pipeline:
            fail(f"production empty route composition missing: {phrase}")
    if "RssAtomRouteProfile(" in pipeline:
        fail("production composition must register zero concrete route profiles")
    composition = contract.get("composition", {})
    if composition.get("production_route_bundles_registered") != 0:
        fail("production route registry must remain empty")
    if composition.get("production_rss_atom_adapters_registered") != 0:
        fail("production public RSS/Atom registry must remain empty")
    if composition.get("production_feed_item_worker_plans_registered") != 0:
        fail("production feed-item worker registry must remain empty")

    for test_name in (
        "test_route_profile_derives_exact_configuration_and_command",
        "test_factory_pins_one_profile_store_adapter_processor_and_registry",
        "test_route_factory_requires_one_readable_and_writable_evidence_store",
        "test_full_public_route_reaches_review_required_feed_item_proposals",
    ):
        if test_name not in tests:
            fail(f"RSS/Atom route test evidence missing: {test_name}")

    for phrase in (
        "exact same parser-profile object",
        "Callers cannot supply an arbitrary configuration hash",
        "Human review remains mandatory",
        "production route registry remains empty",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "RSS Atom route architecture fitness",
        "RSS Atom route behavior",
        "Parent feed item extraction architecture fitness",
        "Parent ingestion worker architecture fitness",
        "check_rss_atom_route_contract.py",
    ):
        if phrase not in workflow:
            fail(f"RSS/Atom route CI step missing: {phrase}")

    print("RSS Atom route contract: PASS")


if __name__ == "__main__":
    main()

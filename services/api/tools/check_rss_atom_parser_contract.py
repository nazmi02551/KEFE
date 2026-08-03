from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "services/api/src/kefe_api/modules/knowledge/rss_atom_parser.py"
TEST = ROOT / "services/api/tests/test_rss_atom_parser.py"
ADR = ROOT / "docs/adr/0088-strict-bounded-rss-atom-parsing-profile.md"
CONTRACT = ROOT / "docs/contracts/rss-atom-parser-slice52.v1.json"
WORKFLOW = ROOT / ".github/workflows/rss-atom-parser-ci.yml"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    for path in (MODULE, TEST, ADR, CONTRACT, WORKFLOW):
        if not path.exists():
            fail(f"missing RSS Atom parser artifact: {path.relative_to(ROOT)}")
    source = MODULE.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    ast.parse(source)

    if contract.get("formats") != ["RSS_2_0", "ATOM_1_0"]:
        fail("feed format profile drifted")
    if contract.get("input", {}).get("network") is not False:
        fail("feed parser must remain network free")
    if contract.get("normalization", {}).get("markup") != "TEXT_ONLY":
        fail("feed parser must remain text only")

    for fragment in (
        "class FeedParseLimits:",
        "class ParsedFeedEntry:",
        "class ParsedFeed:",
        "def parse_rss_atom(",
        "SOURCE_FEED_XML_FORBIDDEN",
        "SOURCE_FEED_LIMIT_EXCEEDED",
        "MappingProxyType",
        "ET.fromstring(document)",
    ):
        if fragment not in source:
            fail(f"parser invariant missing: {fragment}")

    for forbidden in (
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "open(",
        "Path(",
        "lxml",
        "defusedxml",
        "feedparser",
        "while True",
    ):
        if forbidden in source:
            fail(f"forbidden parser dependency or behavior leaked: {forbidden}")

    for evidence in (
        "test_parses_rss_20_in_source_order_and_collapses_markup_text",
        "test_parses_atom_10_with_exact_namespace_and_alternate_links",
        "test_rejects_forbidden_xml_surfaces_before_parsing",
        "test_enforces_depth_element_entry_and_text_limits",
        "test_rejects_entries_without_stable_identity",
    ):
        if evidence not in tests:
            fail(f"parser evidence missing: {evidence}")

    for step in (
        "RSS Atom parser architecture fitness",
        "RSS Atom parser behavior",
        "check_rss_atom_parser_contract.py",
    ):
        if step not in workflow:
            fail(f"RSS Atom CI step missing: {step}")

    print("RSS Atom parser contract: PASS")


if __name__ == "__main__":
    main()

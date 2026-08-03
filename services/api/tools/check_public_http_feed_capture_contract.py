from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "services/api/src/kefe_api/modules/knowledge/public_http_feed_capture.py"
TEST = ROOT / "services/api/tests/test_public_http_feed_capture.py"
ADR = ROOT / "docs/adr/0089-evidence-backed-public-http-feed-capture.md"
CONTRACT = ROOT / "docs/contracts/public-http-feed-capture-slice53.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-http-feed-capture-ci.yml"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    for path in (MODULE, TEST, ADR, CONTRACT, WORKFLOW):
        if not path.exists():
            fail(f"missing public HTTP feed artifact: {path.relative_to(ROOT)}")
    source = MODULE.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tree = ast.parse(source)

    if contract.get("execution", {}).get("credential_mode") != "PUBLIC":
        fail("public HTTP feed credential mode drifted")
    if contract.get("execution", {}).get("secret_access") is not False:
        fail("public HTTP feed adapter cannot access secrets")
    if contract.get("parser", {}).get("runs_after_valid_seal") is not True:
        fail("feed parser must run after evidence seal")

    for fragment in (
        "class PublicHttpFeedCaptureDefinition(Protocol):",
        "class PublicHttpFeedCaptureAdapter:",
        "credential=None",
        "self._evidence_store.seal(",
        "canonical_content_hash(response.body)",
        "parse_rss_atom(",
        "CapturedSource(",
    ):
        if fragment not in source:
            fail(f"public HTTP feed invariant missing: {fragment}")

    seal_position = source.find("seal = self._seal(")
    parse_position = source.find("parsed = parse_rss_atom(", seal_position)
    assembly_position = source.find("return CapturedSource(", parse_position)
    if not 0 <= seal_position < parse_position < assembly_position:
        fail("HTTP feed seal/parse/assembly order drifted")

    for forbidden in (
        "SecretAccess",
        "SecureProviderHttpExecutor",
        "ProviderHttpAuthRegistry",
        "OwnedSensitiveHttpHeaders",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "while True",
    ):
        if forbidden in source:
            fail(f"forbidden public HTTP feed capability leaked: {forbidden}")

    classes = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }
    adapter = classes.get("PublicHttpFeedCaptureAdapter")
    if adapter is None:
        fail("PublicHttpFeedCaptureAdapter is missing")

    for evidence in (
        "test_public_http_feed_capture_uses_no_credential_and_trusted_evidence",
        "test_evidence_failure_precedes_feed_parsing_and_writes_no_artifact",
        "test_strict_parser_rejects_malformed_or_unsupported_body_after_seal",
        "test_http_retryable_and_final_errors_preserve_bounded_codes",
        "test_invalid_plan_mismatch_and_input_fail_closed",
        "test_parse_limits_are_exact_and_snapshotted_at_construction",
    ):
        if evidence not in tests:
            fail(f"public HTTP feed evidence missing: {evidence}")

    for step in (
        "Public HTTP feed architecture fitness",
        "Public HTTP feed behavior",
        "check_public_http_feed_capture_contract.py",
    ):
        if step not in workflow:
            fail(f"public HTTP feed CI step missing: {step}")

    print("public HTTP feed capture contract: PASS")


if __name__ == "__main__":
    main()

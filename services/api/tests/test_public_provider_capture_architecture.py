from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "src/kefe_api/modules/knowledge/provider_public_execution.py"
SECRET = ROOT / "src/kefe_api/modules/knowledge/provider_secret_execution.py"
PIPELINE = ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"
LIVE_RUNTIME = ROOT / "src/kefe_api/infrastructure/canonical_public_feed_runtime.py"


def _class(source: str, name: str) -> ast.ClassDef:
    module = ast.parse(source)
    return next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def test_public_adapter_protocol_has_no_secret_or_transport_capability() -> None:
    source = PUBLIC.read_text()
    adapter = _class(source, "PublicSourceCaptureAdapter")
    capture = next(
        node
        for node in adapter.body
        if isinstance(node, ast.FunctionDef) and node.name == "capture"
    )
    assert tuple(argument.arg for argument in capture.args.args) == ("self",)
    assert tuple(argument.arg for argument in capture.args.kwonlyargs) == (
        "external_locator",
        "trace_id",
        "at",
    )
    for forbidden in (
        "SecretAccess",
        "use_bytes",
        "ProviderHttpAuth",
        "OwnedSensitiveHttpHeaders",
        "RawSourceEvidenceStore",
        "socket",
        "requests",
        "httpx",
        "urllib.request",
    ):
        assert forbidden not in source


def test_credentialed_executor_rejects_public_before_resolver_lookup() -> None:
    source = SECRET.read_text()
    mode_check = source.index(
        "context.credential_mode is not ProviderCredentialMode.SECRET_REF"
    )
    resolver_lookup = source.index("self._resolvers.get_for_reference(secret_ref)")
    assert mode_check < resolver_lookup


def test_production_composition_keeps_public_registry_inert_and_routes_by_mode() -> None:
    pipeline = PIPELINE.read_text()
    runtime = LIVE_RUNTIME.read_text()
    assert "MutablePublicSourceCaptureRegistry()" in pipeline
    assert "class MutablePublicSourceCaptureRegistry(PublicSourceCaptureRegistry):" in runtime
    assert "self._adapters: dict[str, PublicSourceCaptureAdapter] = {}" in runtime
    assert "def register_or_get(" in runtime
    assert "CredentialModeRoutingProviderCaptureExecutor(" in pipeline
    assert "capture_executor=provider_capture_executor" in pipeline
    assert "PublicAdapter(" not in pipeline
    assert "RSS" not in pipeline
    assert "ATOM" not in pipeline

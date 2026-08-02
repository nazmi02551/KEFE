from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "src/kefe_api/modules/knowledge/provider_public_execution.py"
SECRET = ROOT / "src/kefe_api/modules/knowledge/provider_secret_execution.py"
PIPELINE = ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"


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


def test_production_composition_keeps_public_registry_empty_and_routes_by_mode() -> None:
    source = PIPELINE.read_text()
    assert "InMemoryPublicSourceCaptureRegistry()" in source
    assert "CredentialModeRoutingProviderCaptureExecutor(" in source
    assert "capture_executor=provider_capture_executor" in source
    assert "PublicAdapter(" not in source
    assert "RSS" not in source
    assert "ATOM" not in source

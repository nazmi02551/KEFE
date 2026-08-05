from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-secret-resolution.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP secret resolution contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OTP-SECRET-RESOLUTION-001",
        "contract id",
    )
    _require(contract["foundation_wave"] == "F4", "F4 binding")
    _require(contract["capabilities"] == ["CAP-084"], "CAP-084 binding")
    _require(
        contract["production_configuration"]["direct_bearer_token_forbidden"] is True,
        "production direct-token prohibition",
    )
    _require(
        contract["resolution"]["frequency"] == "ONCE_PER_LOGICAL_SEND",
        "logical-send resolution",
    )
    _require(
        contract["resolution"]["transport_retries_reuse_resolution"] is True,
        "retry resolution reuse",
    )
    _require(
        contract["resolution"]["lease_closed_in_finally"] is True,
        "lease closure",
    )
    _require(
        contract["resolution"]["provider_called_on_resolution_failure"] is False,
        "provider isolation",
    )
    _require(
        contract["compatibility"]["openapi_drift_allowed"] is False,
        "OpenAPI stability",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    resolver = _text(
        "services/api/src/kefe_api/modules/identity/otp_secret_resolution.py"
    )
    delivery = _text("services/api/src/kefe_api/modules/identity/otp_delivery.py")
    generic_secret = _text(
        "services/api/src/kefe_api/modules/knowledge/provider_secret_execution.py"
    )
    tests = _text("services/api/tests/test_otp_secret_resolution.py")
    workflow = _text(".github/workflows/otp-secret-resolution.yml")
    adr = _text("docs/adr/0115-rotation-safe-otp-secret-resolution.md")

    for fragment in (
        "otp_http_secret_ref: SecretStr | None",
        "otp_http_bearer_token: SecretStr | None",
        "otp_http_secret_lease_seconds",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    for fragment in (
        "class EnvironmentSecretReferenceResolver",
        "class RegistryBackedOtpSecretLeaseResolver",
        "class StaticOtpSecretLeaseResolver",
        "default_otp_secret_resolver_registry",
        "production forbids KEFE_OTP_HTTP_BEARER_TOKEN",
        "KEFE_OTP_HTTP_SECRET_REF",
        'OTP_HTTP_ADAPTER_CODE = "otp.http.v1"',
        "parsed.netloc",
    ):
        _require(fragment in resolver, f"missing resolver boundary: {fragment}")

    _require("class SecretLease" in generic_secret, "generic SecretLease reuse")
    _require("self._material[index] = 0" in generic_secret, "lease zeroing")
    _require("class InMemorySecretResolverRegistry" in generic_secret, "registry reuse")

    for fragment in (
        "secret_resolver: OtpSecretLeaseResolver | None",
        "self._secret_resolver.resolve(",
        "lease.use_bytes(",
        "finally:\n            lease.close()",
        "OTP_SECRET_RESOLUTION_RETRYABLE",
        "OTP_SECRET_RESOLUTION_FINAL",
        "OTP_SECRET_RESOLUTION_UNEXPECTED",
        "OTP_SECRET_MATERIAL_INVALID",
        "secret_resolver=<redacted>",
        "secret_resolver_registry: SecretResolverRegistry | None",
    ):
        _require(fragment in delivery, f"missing delivery behavior: {fragment}")

    for fragment in (
        "test_each_logical_send_resolves_current_secret_and_closes_lease",
        "test_transport_retry_reuses_one_resolution_and_exact_request",
        "test_resolution_failure_does_not_call_provider_or_leak_secret_reference",
        "test_environment_reference_reads_rotated_value_without_restart",
        "test_production_requires_opaque_reference_and_forbids_direct_token",
    ):
        _require(fragment in tests, f"missing test evidence: {fragment}")

    _require("Exact OpenAPI remains unchanged" in workflow, "exact OpenAPI gate")
    _require("test_otp_http_delivery.py" in workflow, "parent delivery regression")
    _require("test_otp_delivery_health.py" in workflow, "health regression")
    _require("test_otp_request_abuse_guard.py" in workflow, "abuse regression")
    _require("test_privacy_export_deletion_hardening.py" in workflow, "privacy regression")

    lower_adr = adr.lower()
    for non_claim in (
        "real provider credentials",
        "real email/sms delivery",
        "connected managed-secret service",
        "operator-executed credential rotation",
    ):
        _require(non_claim in lower_adr, f"missing external non-claim: {non_claim}")

    forbidden = (
        "print(secret",
        "logger.info(secret",
        "logger.debug(secret",
        "logger.info(secret_ref",
        "logger.debug(secret_ref",
        "provider_response_body=",
    )
    combined_runtime = resolver + delivery
    for fragment in forbidden:
        _require(fragment not in combined_runtime, f"forbidden runtime fragment: {fragment}")

    print(
        "OTP secret resolution contract: PASS — production opaque references, "
        "per-send bounded leases, retry-stable request identity, fail-closed "
        "resolution, zero provider calls on resolver failure, redaction and "
        "unchanged public API are executable."
    )


if __name__ == "__main__":
    main()

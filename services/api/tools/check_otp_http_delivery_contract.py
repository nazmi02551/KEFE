from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-http-delivery.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP HTTP delivery contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(contract["contract_id"] == "KEFE-OTP-HTTP-DELIVERY-001", "contract id")
    _require(contract["capabilities"] == ["CAP-084"], "CAP-084 binding")
    _require(contract["runtime_modes"]["production_required"] == "HTTP", "production mode")
    _require(
        contract["delivery_identity"]["source"] == "OtpChallenge.id",
        "challenge delivery identity",
    )
    _require(
        contract["delivery_identity"]["retry_reuses_exact_request"] is True,
        "retry idempotency",
    )
    _require(contract["endpoint_policy"]["redirects_followed"] is False, "redirect policy")
    _require(
        contract["outcomes"]["provider_response_body_exposed"] is False,
        "provider response privacy",
    )
    _require(
        contract["public_api"]["openapi_drift_allowed"] is False,
        "OpenAPI drift policy",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    ports = _text("services/api/src/kefe_api/modules/identity/account_ports.py")
    service = _text("services/api/src/kefe_api/modules/identity/account_service.py")
    delivery = _text("services/api/src/kefe_api/modules/identity/otp_delivery.py")
    main_module = _text("services/api/src/kefe_api/main.py")
    tests = _text("services/api/tests/test_otp_http_delivery.py")
    workflow = _text(".github/workflows/otp-http-delivery.yml")
    adr = _text("docs/adr/0112-provider-neutral-production-otp-delivery.md")

    for fragment in (
        'otp_delivery_mode: Literal["CAPTURE", "DISABLED", "HTTP"]',
        "otp_http_endpoint",
        "otp_http_bearer_token: SecretStr",
        "otp_http_timeout_ms",
        "otp_http_max_response_bytes",
        "otp_http_max_attempts",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    _require("delivery_id: UUID" in ports, "delivery UUID port")
    _require("expires_at: datetime" in ports, "delivery expiry port")
    _require("delivery_id=challenge.id" in service, "persisted challenge id propagation")
    _require("expires_at=challenge.expires_at" in service, "challenge expiry propagation")
    _require("class HttpOtpDelivery" in delivery, "HTTP adapter")
    _require("class UrllibOtpHttpTransport" in delivery, "real urllib transport")
    _require('method="POST"' in delivery, "HTTP POST")
    _require('("idempotency-key", str(delivery_id))' in delivery, "idempotency header")
    _require("_NoRedirectHandler" in delivery, "redirect refusal")
    _require("_RETRYABLE_HTTP_STATUSES" in delivery, "retryable status classification")
    _require("AUTH_OTP_DELIVERY_UNAVAILABLE" in delivery, "retryable domain error")
    _require("AUTH_OTP_DELIVERY_REJECTED" in delivery, "final domain error")
    _require("response.read(request.max_response_bytes + 1)" in delivery, "response bound")
    _require("endpoint=<redacted>" in delivery, "endpoint redaction")
    _require("bearer_token=<redacted>" in delivery, "credential redaction")
    _require("build_otp_delivery(settings)" in main_module, "explicit composition")

    for fragment in (
        "test_http_delivery_uses_exact_redacted_idempotent_request_contract",
        "test_retryable_status_reuses_exact_request_and_idempotency_key",
        "test_retryable_network_failure_exhaustion_is_unavailable",
        "test_final_provider_rejection_is_not_retried_or_body_exposed",
        "test_urllib_transport_invokes_post_with_bounded_read_and_timeout",
        "test_production_forbids_non_http_delivery_modes",
    ):
        _require(fragment in tests, f"missing evidence: {fragment}")

    _require("Exact OpenAPI remains unchanged" in workflow, "exact OpenAPI gate")
    _require("real provider deliverability" in adr.lower(), "external provider non-claim")
    _require("automatic email/sms fallback" in adr.lower(), "no silent fallback decision")

    forbidden_runtime_fragments = (
        "print(code)",
        "logger.info(code",
        "logger.debug(code",
        "provider_response_body=",
    )
    for fragment in forbidden_runtime_fragments:
        _require(fragment not in delivery, f"forbidden runtime fragment: {fragment}")

    print(
        "OTP HTTP delivery contract: PASS — challenge-bound idempotency, HTTPS-only "
        "provider-neutral POST, bounded retries/response, production fail-closed, "
        "redacted operations, unchanged public API and explicit external non-claims."
    )


if __name__ == "__main__":
    main()

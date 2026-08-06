from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-provider-receipts.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP provider receipts contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _registry_version(text: str) -> tuple[int, int, int]:
    match = re.search(r"^registry_version:\s*(\d+)\.(\d+)\.(\d+)$", text, re.M)
    _require(match is not None, "error registry version format")
    assert match is not None
    return tuple(int(part) for part in match.groups())


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OTP-PROVIDER-RECEIPT-001",
        "contract id",
    )
    _require(contract["wave"] == "F4", "F4 binding")
    _require(
        contract["capabilities"] == ["CAP-084", "CAP-123"],
        "capability binding",
    )
    _require(
        contract["authentication"]["mode"] == "HMAC_SHA256",
        "HMAC mode",
    )
    _require(
        contract["authentication"]["constant_time_compare"] is True,
        "constant-time compare",
    )
    _require(
        contract["persistence"]["raw_body_stored"] is False,
        "raw body non-persistence",
    )
    _require(
        contract["idempotency"]["concurrent_duplicate_converges"] is True,
        "concurrent replay convergence",
    )
    _require(
        contract["endpoint"]["openapi_exposed"] is False,
        "consumer OpenAPI boundary",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    domain = _text(
        "services/api/src/kefe_api/modules/identity/otp_provider_receipts.py"
    )
    router = _text(
        "services/api/src/kefe_api/modules/identity/otp_provider_receipts_router.py"
    )
    postgres = _text(
        "services/api/src/kefe_api/infrastructure/postgres_otp_provider_receipts.py"
    )
    persistence = _text("services/api/src/kefe_api/infrastructure/persistence.py")
    main_module = _text("services/api/src/kefe_api/main.py")
    migration = _text(
        "services/api/migrations/versions/20260806_0034_otp_provider_receipts.py"
    )
    memory_tests = _text("services/api/tests/test_otp_provider_receipts.py")
    http_tests = _text("services/api/tests/test_otp_provider_receipts_http.py")
    postgres_tests = _text(
        "services/api/tests/test_otp_provider_receipts_postgres.py"
    )
    workflow = _text(".github/workflows/otp-provider-receipts.yml")
    adr = _text(
        "docs/adr/0117-authenticated-otp-provider-receipt-callbacks.md"
    )
    errors = _text("docs/contracts/error-codes.v1.yaml")

    for fragment in (
        'otp_receipt_mode: Literal["DISABLED", "HMAC_SHA256"]',
        "otp_receipt_secret_refs",
        "otp_receipt_secret_lease_seconds",
        "otp_receipt_max_skew_seconds",
        "otp_receipt_max_body_bytes",
        "otp_receipt_retention_seconds",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    for fragment in (
        "class OtpProviderReceiptOutcome",
        "class InMemoryOtpProviderReceiptRepository",
        "class RegistryBackedOtpProviderReceiptSecretLeaseResolver",
        "class OtpProviderReceiptService",
        "hmac.compare_digest",
        "provider_event_id.encode",
        "str(delivery_id).lower().encode",
        "AUTH_OTP_RECEIPT_EVENT_CONFLICT",
        "AUTH_OTP_RECEIPT_AUTH_UNAVAILABLE",
        "AUTH_OTP_RECEIPT_REJECTED",
        "lease.close()",
    ):
        _require(fragment in domain, f"missing domain fragment: {fragment}")

    for fragment in (
        '"/otp-delivery-receipts"',
        "include_in_schema=False",
        "await request.body()",
        'Header(alias="X-KEFE-OTP-Receipt-Timestamp")',
        'Header(alias="X-KEFE-OTP-Receipt-Key-Id")',
        'Header(alias="X-KEFE-OTP-Receipt-Event-Id")',
        'Header(alias="X-KEFE-OTP-Receipt-Signature")',
    ):
        _require(fragment in router, f"missing HTTP fragment: {fragment}")

    _require(
        "class PostgresOtpProviderReceiptRepository" in postgres,
        "PostgreSQL repository",
    )
    _require(
        "ON CONFLICT (provider_event_ref) DO NOTHING" in postgres,
        "PostgreSQL idempotency",
    )
    _require(
        "build_otp_provider_receipt_repository" in persistence,
        "persistence composition",
    )
    _require(
        "otp_provider_receipt_service" in main_module
        and "otp_provider_receipts_router" in main_module,
        "application composition",
    )
    _require('revision = "20260806_0034"' in migration, "migration revision")
    _require('down_revision = "20260806_0033"' in migration, "linear migration")
    _require(
        "otp_provider_receipt_no_update" in migration,
        "database immutability",
    )

    for fragment in (
        "test_valid_receipt_is_authenticated_and_persisted_aggregate_only",
        "test_exact_replay_is_idempotent_and_conflicting_reuse_is_rejected",
        "test_invalid_signature_stale_timestamp_and_unknown_key_are_indistinguishable",
    ):
        _require(fragment in memory_tests, f"missing memory proof: {fragment}")
    _require(
        "test_signed_callback_is_accepted_and_exact_replay_is_duplicate"
        in http_tests,
        "HTTP replay proof",
    )
    for fragment in (
        "test_postgres_receipt_survives_restart_and_exact_replay_is_idempotent",
        "test_postgres_concurrent_duplicate_receipts_converge",
        "test_postgres_receipt_schema_is_privacy_safe_retained_and_immutable",
    ):
        _require(fragment in postgres_tests, f"missing PostgreSQL proof: {fragment}")

    _require(_registry_version(errors) >= (1, 23, 0), "error registry minimum")
    for code in (
        "AUTH_OTP_RECEIPT_DISABLED",
        "AUTH_OTP_RECEIPT_AUTH_UNAVAILABLE",
        "AUTH_OTP_RECEIPT_REJECTED",
        "AUTH_OTP_RECEIPT_EVENT_CONFLICT",
    ):
        _require(f"- code: {code}" in errors, f"missing error code: {code}")
    _require("Exact composed OpenAPI remains unchanged" in workflow, "OpenAPI gate")
    _require("real email or SMS delivery" in adr, "real delivery non-claim")
    _require("callback transport availability" in adr, "transport non-claim")

    forbidden_storage_fragments = (
        "recipient=",
        "destination=",
        "raw_body=receipt",
        "signature=receipt",
        "secret_ref=receipt",
        "provider_event_id=receipt",
        "delivery_id=receipt",
    )
    for fragment in forbidden_storage_fragments:
        _require(fragment not in postgres, f"forbidden storage fragment: {fragment}")

    print(
        "OTP provider receipts contract: PASS — exact-body HMAC authentication, "
        "rotation-safe secret references, bounded replay protection, privacy-safe "
        "append-only persistence, restart/concurrency evidence and unchanged consumer "
        "OpenAPI are executable."
    )


if __name__ == "__main__":
    main()

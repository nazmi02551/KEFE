from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-request-abuse-guard.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP request abuse guard contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OTP-REQUEST-ABUSE-GUARD-001",
        "contract id",
    )
    _require(contract["capabilities"] == ["CAP-084"], "CAP-084 binding")
    _require(contract["foundation_wave"] == "F4", "F4 binding")
    _require(
        contract["runtime_modes"]["AUTO"]["production"] == "ENFORCE",
        "AUTO production mode",
    )
    _require(
        contract["runtime_modes"]["OFF"]["production_allowed"] is False,
        "production fail-closed",
    )
    limited = contract["public_api"]["limited_error"]
    _require(limited["code"] == "AUTH_RATE_LIMITED", "limited error code")
    _require(limited["http_status"] == 429, "limited HTTP status")
    _require(limited["retryable"] is True, "limited retryability")
    _require(
        contract["admission_identity"]["normalization_precedes_hashing"] is True,
        "normalization before hashing",
    )
    _require(
        contract["admission_identity"]["plaintext_destination_persisted"] is False,
        "plaintext destination policy",
    )
    _require(
        contract["policy"]["provider_failure_consumes_admission"] is True,
        "provider failure admission",
    )
    _require(
        contract["postgres"]["guard_and_challenge_single_transaction"] is True,
        "atomic guard and challenge",
    )
    _require(
        contract["postgres"]["rejected_challenge_insert_rolled_back"] is True,
        "rejected challenge rollback",
    )
    _require(
        contract["privacy"][
            "account_privacy_deletion_cascades_via_latest_challenge"
        ]
        is True,
        "privacy deletion cascade",
    )
    _require(
        contract["public_api"]["openapi_drift_allowed"] is False,
        "OpenAPI drift policy",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    persistence = _text("services/api/src/kefe_api/infrastructure/persistence.py")
    memory = _text("services/api/src/kefe_api/modules/identity/otp_request_guard.py")
    postgres = _text(
        "services/api/src/kefe_api/infrastructure/postgres_otp_request_guard.py"
    )
    migration = _text(
        "services/api/migrations/versions/20260805_0031_otp_request_abuse_guard.py"
    )
    service = _text("services/api/src/kefe_api/modules/identity/account_service.py")
    memory_tests = _text("services/api/tests/test_otp_request_abuse_guard.py")
    postgres_tests = _text(
        "services/api/tests/test_otp_request_abuse_guard_postgres.py"
    )
    error_registry = _text("docs/contracts/error-codes.v1.yaml")
    workflow = _text(".github/workflows/otp-request-abuse-guard.yml")
    adr = _text("docs/adr/0113-durable-otp-request-abuse-guard.md")

    for fragment in (
        'otp_request_guard_mode: Literal["AUTO", "OFF", "ENFORCE"]',
        "otp_request_cooldown_seconds",
        "otp_request_window_seconds",
        "otp_request_window_limit",
        "otp_request_guard_retention_seconds",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    for fragment in (
        "GuardedInMemoryAccountContinuityRepository",
        "GuardedPostgresAccountContinuityRepository",
        'mode == "ENFORCE" or (mode == "AUTO" and production)',
        "production forbids KEFE_OTP_REQUEST_GUARD_MODE=OFF",
    ):
        _require(fragment in persistence, f"missing composition fragment: {fragment}")

    for fragment in (
        "class OtpRequestAbusePolicy",
        "window_seconds < cooldown_seconds",
        "retention_seconds < window_seconds",
        "class GuardedInMemoryAccountContinuityRepository",
        "with self._lock",
        "otp_request_rate_limited_error()",
    ):
        _require(fragment in memory, f"missing memory guard fragment: {fragment}")

    for fragment in (
        "class GuardedPostgresAccountContinuityRepository",
        "DELETE FROM identity.otp_request_guard",
        "INSERT INTO identity.otp_challenge",
        "ON CONFLICT (channel, identifier_hash) DO NOTHING",
        "FOR UPDATE",
        "UPDATE identity.otp_request_guard",
        "otp_request_rate_limited_error()",
    ):
        _require(fragment in postgres, f"missing PostgreSQL fragment: {fragment}")

    _require(
        postgres.index("INSERT INTO identity.otp_challenge")
        < postgres.index("INSERT INTO identity.otp_request_guard"),
        "challenge must be inserted before guard admission in one transaction",
    )
    _require("delivery_id=challenge.id" in service, "challenge identity delivery")
    _require(
        "self._repo.create_challenge(challenge)" in service,
        "guarded challenge repository boundary",
    )
    _require(
        service.index("self._repo.create_challenge(challenge)")
        < service.index("self._delivery.send("),
        "admission must precede delivery",
    )

    for fragment in (
        'revision = "20260805_0031"',
        'down_revision = "20260805_0030"',
        "CREATE TABLE identity.otp_request_guard",
        "PRIMARY KEY (channel, identifier_hash)",
        "REFERENCES identity.otp_challenge(id) ON DELETE CASCADE",
        "otp_request_guard_retention_idx",
    ):
        _require(fragment in migration, f"missing migration fragment: {fragment}")

    _require(
        "- code: AUTH_RATE_LIMITED\n  http_status: 429\n  retryable: true"
        in error_registry,
        "registered AUTH_RATE_LIMITED error",
    )

    for fragment in (
        "test_auto_mode_is_compatible_in_development_and_enforced_in_production",
        "test_production_cannot_disable_otp_request_guard",
        "test_normalized_destination_is_limited_before_second_delivery",
        "test_delivery_failure_still_consumes_destination_quota",
        "test_concurrent_memory_requests_admit_exactly_one_delivery",
        "test_http_surface_returns_registered_retryable_problem",
    ):
        _require(fragment in memory_tests, f"missing memory evidence: {fragment}")

    for fragment in (
        "test_postgres_guard_survives_application_restart",
        "test_postgres_concurrent_requests_admit_one_challenge",
        "test_privacy_deletion_cascades_destination_guard",
        "test_guard_schema_contains_only_hashes_and_operational_timestamps",
    ):
        _require(fragment in postgres_tests, f"missing PostgreSQL evidence: {fragment}")

    _require("Exact OpenAPI remains unchanged" in workflow, "exact OpenAPI gate")
    _require("alembic upgrade head" in workflow, "migration gate")
    _require("real-world abuse resistance" in adr, "external abuse non-claim")
    _require("CAPTCHA" in adr, "CAPTCHA decision boundary")
    _require("production threshold quality" in adr, "threshold non-claim")

    forbidden_migration_fragments = (
        "plaintext_destination",
        "identifier_hint",
        "otp_code",
        "provider_request",
        "provider_response",
    )
    for fragment in forbidden_migration_fragments:
        _require(fragment not in migration, f"forbidden migration field: {fragment}")

    print(
        "OTP request abuse guard contract: PASS — normalized hash identity, "
        "production fail-closed composition, cooldown/window admission, atomic "
        "PostgreSQL challenge persistence, concurrency convergence, bounded privacy "
        "retention, deletion cascade, registered retryable 429 and unchanged OpenAPI."
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-delivery-health.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP delivery health contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OTP-DELIVERY-HEALTH-001",
        "contract id",
    )
    _require(
        contract["capabilities"] == ["CAP-084", "CAP-123"],
        "capability binding",
    )
    _require(contract["foundation_wave"] == "F4", "F4 binding")
    _require(
        contract["source_boundary"]["provider_call_repeated_for_observation_failure"]
        is False,
        "no duplicate provider call",
    )
    _require(
        contract["source_boundary"]["provider_result_replaced_by_observation_failure"]
        is False,
        "provider result authority",
    )
    _require(contract["event"]["append_only"] is True, "append-only event model")
    _require(contract["event"]["foreign_keys"] is False, "no identity linkage")
    _require(
        contract["snapshot"]["ratio_suppressed_below_minimum_sample"] is True,
        "minimum sample rule",
    )
    _require(
        contract["snapshot"]["quiet_claims_provider_health"] is False,
        "quiet non-claim",
    )
    _require(
        contract["admin_integration"]["http_response_shape_changed"] is False,
        "Admin response stability",
    )
    _require(
        contract["admin_integration"]["openapi_drift_allowed"] is False,
        "OpenAPI drift policy",
    )
    _require(
        contract["failure_isolation"]["duplicate_send_on_observation_failure"]
        is False,
        "observation failure isolation",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    persistence = _text("services/api/src/kefe_api/infrastructure/persistence.py")
    domain = _text(
        "services/api/src/kefe_api/modules/identity/otp_delivery_health.py"
    )
    postgres = _text(
        "services/api/src/kefe_api/infrastructure/postgres_otp_delivery_health.py"
    )
    migration = _text(
        "services/api/migrations/versions/20260805_0032_otp_delivery_health.py"
    )
    main_source = _text("services/api/src/kefe_api/main.py")
    admin_models = _text(
        "services/api/src/kefe_api/modules/admin_operational_reports/models.py"
    )
    admin_service = _text(
        "services/api/src/kefe_api/modules/admin_operational_reports/service.py"
    )
    admin_router = _text(
        "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py"
    )
    memory_tests = _text("services/api/tests/test_otp_delivery_health.py")
    postgres_tests = _text(
        "services/api/tests/test_otp_delivery_health_postgres.py"
    )
    workflow = _text(".github/workflows/otp-delivery-health.yml")
    adr = _text("docs/adr/0114-durable-otp-delivery-health.md")

    for fragment in (
        "otp_delivery_health_window_seconds",
        "otp_delivery_health_retention_seconds",
        "otp_delivery_health_minimum_ratio_sample",
        "otp_delivery_health_failure_attention",
        "otp_delivery_health_failure_critical",
        "otp_delivery_health_unavailable_attention",
        "otp_delivery_health_unavailable_critical",
        "otp_delivery_health_ratio_attention_bps",
        "otp_delivery_health_ratio_critical_bps",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    for fragment in (
        "class OtpDeliveryHealthSignal",
        "class OtpDeliveryHealthEvent",
        "class OtpDeliveryHealthPolicy",
        "class OtpDeliveryHealthSnapshot",
        "class InMemoryOtpDeliveryHealthRepository",
        "class DurableOtpDeliveryObserver",
        "class FailOpenOtpDeliveryObserver",
        "class OtpDeliveryHealthService",
        "facts.total_count >= resolved_policy.minimum_ratio_sample",
        'reason.endswith("_CRITICAL")',
    ):
        _require(fragment in domain, f"missing domain fragment: {fragment}")

    _require(
        "except Exception" in domain
        and "OTP delivery health observation failed" in domain,
        "fail-open observation wrapper",
    )
    _require(
        "self._delegate.record(result)" in domain,
        "delegate observation call",
    )

    for fragment in (
        "PostgresOtpDeliveryHealthRepository",
        "DELETE FROM identity.otp_delivery_event",
        "INSERT INTO identity.otp_delivery_event",
        "count(*) FILTER (WHERE outcome = 'ACCEPTED')",
        "max(observed_at) FILTER (WHERE outcome = 'ACCEPTED')",
    ):
        _require(fragment in postgres, f"missing PostgreSQL fragment: {fragment}")

    for fragment in (
        'revision = "20260805_0032"',
        'down_revision = "20260805_0031"',
        "CREATE TABLE identity.otp_delivery_event",
        "otp_delivery_event_observed_idx",
        "otp_delivery_event_outcome_idx",
    ):
        _require(fragment in migration, f"missing migration fragment: {fragment}")

    forbidden_storage = tuple(contract["event"]["forbidden_fields"])
    for fragment in forbidden_storage:
        _require(fragment not in migration, f"forbidden persisted field: {fragment}")
    _require("REFERENCES" not in migration, "event table must not have foreign keys")

    _require(
        "build_otp_delivery_health_repository" in persistence
        and "PostgresOtpDeliveryHealthRepository" in persistence
        and "InMemoryOtpDeliveryHealthRepository" in persistence,
        "repository composition",
    )
    for fragment in (
        "OtpDeliveryHealthPolicy.from_seconds",
        "DurableOtpDeliveryObserver",
        "FailOpenOtpDeliveryObserver",
        "build_otp_delivery(settings,",
        "observer=otp_delivery_health_observer",
        "otp_delivery_health=otp_delivery_health_service",
    ):
        _require(fragment in main_source, f"missing runtime composition: {fragment}")

    for fragment in (
        "OTP_DELIVERY_ATTENTION",
        "OTP_DELIVERY_CRITICAL",
        "otp_delivery: OtpDeliveryHealthPolicy",
        "otp_delivery: OtpDeliveryHealthSnapshot",
    ):
        _require(fragment in admin_models, f"missing Admin model fragment: {fragment}")
    for fragment in (
        "otp_delivery_health.snapshot",
        "OtpDeliveryHealthSignal.CRITICAL",
        "OtpDeliveryHealthSignal.ATTENTION",
        "AdminOperationalReason.OTP_DELIVERY_CRITICAL",
        "AdminOperationalReason.OTP_DELIVERY_ATTENTION",
    ):
        _require(fragment in admin_service, f"missing Admin service fragment: {fragment}")
    _require(
        "otp_delivery" not in admin_router,
        "detailed OTP snapshot must not be exposed by Admin HTTP response",
    )

    for fragment in (
        "test_health_snapshot_distinguishes_quiet_nominal_attention_and_critical",
        "test_failure_ratio_is_suppressed_below_minimum_sample",
        "test_snapshot_prunes_events_outside_retention",
        "test_fail_open_observer_never_masks_provider_success_or_error",
        "test_secured_admin_report_surfaces_only_aggregate_critical_reason",
    ):
        _require(fragment in memory_tests, f"missing memory evidence: {fragment}")
    for fragment in (
        "test_postgres_delivery_health_survives_application_restart",
        "test_postgres_snapshot_prunes_events_outside_retention",
        "test_postgres_aggregate_thresholds_are_deterministic",
        "test_postgres_health_schema_is_privacy_safe_and_append_only",
    ):
        _require(fragment in postgres_tests, f"missing PostgreSQL evidence: {fragment}")

    _require("Exact OpenAPI remains unchanged" in workflow, "exact OpenAPI gate")
    _require("alembic upgrade head" in workflow, "migration gate")
    _require("provider acceptance is not deliverability" in adr.lower(), "deliverability non-claim")
    _require("telemetry completeness" in adr, "telemetry completeness non-claim")
    _require("Quiet means" in adr, "quiet semantics")

    print(
        "OTP delivery health contract: PASS — final provider-neutral outcomes, "
        "fail-open observation, privacy-safe append-only events, bounded retention, "
        "minimum-sample signal policy, restart durability, aggregate secured Admin "
        "reason codes and unchanged OpenAPI."
    )


if __name__ == "__main__":
    main()

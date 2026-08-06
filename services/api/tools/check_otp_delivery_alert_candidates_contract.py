from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/otp-delivery-alert-candidates.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"OTP delivery alert candidates contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _registry_version(text: str) -> tuple[int, int, int]:
    match = re.search(
        r"^registry_version:\s*(\d+)\.(\d+)\.(\d+)$",
        text,
        re.M,
    )
    _require(match is not None, "error registry version format")
    assert match is not None
    return tuple(int(part) for part in match.groups())


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OTP-ALERT-CANDIDATES-001",
        "contract id",
    )
    _require(contract["foundation_wave"] == "F4", "F4 binding")
    _require(contract["capabilities"] == ["CAP-123"], "CAP-123 binding")
    _require(
        contract["source"]["eligible_signals"] == ["ATTENTION", "CRITICAL"],
        "eligible signals",
    )
    _require(contract["source"]["background_polling"] is False, "no polling")
    _require(
        contract["deduplication"]["same_or_higher_severity_suppressed"] is True,
        "severity cooldown",
    )
    _require(
        contract["deduplication"]["attention_to_critical_escalation_immediate"]
        is True,
        "immediate escalation",
    )
    _require(contract["candidate"]["immutable"] is True, "candidate immutability")
    _require(
        contract["acknowledgement"]["free_text_allowed"] is False,
        "no free text acknowledgement",
    )
    _require(
        contract["acknowledgement"]["means_resolution"] is False,
        "acknowledgement non-resolution",
    )
    _require(
        contract["failure_isolation"]["candidate_failure_retries_provider_send"]
        is False,
        "no provider resend",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    domain = _text(
        "services/api/src/kefe_api/modules/identity/otp_delivery_health.py"
    )
    postgres = _text(
        "services/api/src/kefe_api/infrastructure/postgres_otp_delivery_health.py"
    )
    persistence = _text("services/api/src/kefe_api/infrastructure/persistence.py")
    migration = _text(
        "services/api/migrations/versions/20260806_0033_otp_delivery_alert_candidates.py"
    )
    admin_models = _text(
        "services/api/src/kefe_api/modules/admin_security/models.py"
    )
    admin_policy = _text(
        "services/api/src/kefe_api/modules/admin_security/policy.py"
    )
    secured = _text(
        "services/api/src/kefe_api/modules/admin_security/operational_reports.py"
    )
    router = _text(
        "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py"
    )
    memory_tests = _text(
        "services/api/tests/test_otp_delivery_alert_candidates.py"
    )
    http_tests = _text("services/api/tests/test_otp_delivery_alerts_http.py")
    postgres_tests = _text(
        "services/api/tests/test_otp_delivery_alert_candidates_postgres.py"
    )
    workflow = _text(".github/workflows/otp-delivery-alert-candidates.yml")
    adr = _text(
        "docs/adr/0116-durable-otp-alert-candidates-and-acknowledgement.md"
    )
    error_codes = _text("docs/contracts/error-codes.v1.yaml")

    for fragment in (
        "otp_delivery_alert_cooldown_seconds",
        "otp_delivery_alert_retention_seconds",
    ):
        _require(fragment in settings, f"missing setting: {fragment}")

    for fragment in (
        "class OtpDeliveryAlertPolicy",
        "class OtpDeliveryAlertCandidate",
        "class OtpDeliveryAlertAcknowledgement",
        "class OtpDeliveryAlertRecord",
        "def list_alert_candidates(",
        "def acknowledge_alert(",
        "_append_alert_candidate_if_due_locked",
        "_signal_rank(candidate.signal) >= current_rank",
        "self._alert_acknowledgements.setdefault",
        '"ADMIN_OPERATIONAL_ALERT_NOT_FOUND"',
    ):
        _require(fragment in domain, f"missing domain fragment: {fragment}")

    for fragment in (
        "pg_advisory_xact_lock",
        "_create_alert_candidate_if_due",
        "ON CONFLICT (candidate_id) DO NOTHING",
        "identity.otp_delivery_alert_candidate",
        "identity.otp_delivery_alert_acknowledgement",
        "DELETE FROM identity.otp_delivery_alert_candidate",
    ):
        _require(fragment in postgres, f"missing PostgreSQL fragment: {fragment}")
    _require("UPDATE identity.otp_delivery_alert" not in postgres, "repository update path")

    for fragment in (
        "_otp_delivery_alert_policy",
        "OtpDeliveryAlertPolicy.from_seconds",
        "health_policy=health_policy",
        "alert_policy=alert_policy",
    ):
        _require(fragment in persistence, f"missing composition fragment: {fragment}")

    for fragment in (
        'revision = "20260806_0033"',
        'down_revision = "20260805_0032"',
        "CREATE TABLE identity.otp_delivery_alert_candidate",
        "CREATE TABLE identity.otp_delivery_alert_acknowledgement",
        "otp_delivery_alert_candidate_no_update",
        "otp_delivery_alert_acknowledgement_no_update",
        "ON DELETE CASCADE",
    ):
        _require(fragment in migration, f"missing migration fragment: {fragment}")

    for forbidden in contract["privacy"]["forbidden_fields"]:
        _require(forbidden not in migration, f"forbidden persisted field: {forbidden}")

    _require(
        "OPERATIONAL_ALERT_ACKNOWLEDGE" in admin_models,
        "dedicated Admin capability",
    )
    _require(
        "AdminCapability.OPERATIONAL_ALERT_ACKNOWLEDGE" in admin_policy,
        "capability grant and step-up policy",
    )
    _require(
        admin_policy.count("AdminCapability.OPERATIONAL_ALERT_ACKNOWLEDGE") >= 3,
        "role grants plus step-up registration",
    )
    for fragment in (
        "AdminCapability.OPERATIONAL_REPORT_READ",
        "AdminCapability.OPERATIONAL_ALERT_ACKNOWLEDGE",
        "principal.audit_actor_ref",
    ):
        _require(fragment in secured, f"missing secured fragment: {fragment}")

    for fragment in (
        '"/otp-delivery-alerts"',
        '"/otp-delivery-alerts/{candidate_id}/acknowledgement"',
        "WritePrincipalDep",
        "expected_candidate_id",
        'Literal["ACKNOWLEDGE"]',
        '"ADMIN_OPERATIONAL_ALERT_ACK_MISMATCH"',
        "acknowledgement_is_resolution: bool = False",
        "aggregate_only: bool = True",
    ):
        _require(fragment in router, f"missing Admin HTTP fragment: {fragment}")
    for forbidden in ("note:", "rationale:", "message:", "comment:"):
        _require(forbidden not in router, f"free-text acknowledgement field: {forbidden}")

    for fragment in (
        "test_alert_candidates_deduplicate_equal_severity_and_allow_escalation",
        "test_nominal_delivery_does_not_create_alert_candidate",
        "test_acknowledgement_is_idempotent_and_never_means_resolution",
        "test_alert_candidate_records_are_aggregate_only_and_privacy_safe",
    ):
        _require(fragment in memory_tests, f"missing memory evidence: {fragment}")
    for fragment in (
        "test_alert_list_requires_operational_report_read_and_is_bounded",
        "test_acknowledgement_requires_capability_csrf_step_up_and_exact_candidate",
        "test_acknowledgement_is_idempotent_privacy_safe_and_not_resolution",
        "test_snapshot_read_never_creates_alert_candidate",
    ):
        _require(fragment in http_tests, f"missing HTTP evidence: {fragment}")
    for fragment in (
        "test_postgres_alert_candidates_survive_restart_and_escalate",
        "test_postgres_concurrent_candidate_admission_is_deduplicated",
        "test_postgres_acknowledgement_is_restart_durable_and_idempotent",
        "test_postgres_alert_retention_prunes_candidate_and_acknowledgement",
        "test_postgres_alert_schema_is_aggregate_only_and_update_immutable",
    ):
        _require(fragment in postgres_tests, f"missing PostgreSQL evidence: {fragment}")

    _require(
        _registry_version(error_codes) >= (1, 22, 0),
        "error registry minimum version",
    )
    for fragment in (
        "- code: ADMIN_OPERATIONAL_ALERT_NOT_FOUND\n  http_status: 404",
        "- code: ADMIN_OPERATIONAL_ALERT_ACK_MISMATCH\n  http_status: 409",
    ):
        _require(fragment in error_codes, f"missing registered error: {fragment}")

    for fragment in (
        "Executable parent OTP delivery health contract",
        "Executable OTP alert candidate contract",
        "Exact Operational Reports OpenAPI overlay",
        "Full composed OpenAPI drift gate",
        "alembic upgrade head",
    ):
        _require(fragment in workflow, f"missing CI gate: {fragment}")

    lower_adr = adr.lower()
    for non_claim in (
        "external paging",
        "email/slack notification",
        "automated remediation",
        "provider delivery receipts",
        "operator response effectiveness",
    ):
        _require(non_claim in lower_adr, f"missing external non-claim: {non_claim}")

    combined_runtime = domain + postgres + router
    for forbidden in (
        "print(recipient",
        "logger.info(recipient",
        "logger.debug(recipient",
        "provider_response_body=",
        "otp_code=",
    ):
        _require(forbidden not in combined_runtime, f"forbidden runtime leak: {forbidden}")

    print(
        "OTP delivery alert candidates contract: PASS — aggregate degraded-state "
        "candidates, severity cooldown, immediate escalation, restart durability, "
        "immutable idempotent acknowledgement, dedicated step-up Admin capability, "
        "privacy-safe storage and explicit external non-claims are executable."
    )


if __name__ == "__main__":
    main()

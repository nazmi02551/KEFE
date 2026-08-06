from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/operational-readiness-evidence.v1.json"

EXPECTED_ITEM_IDS = {
    "admin-operational-reports",
    "otp-delivery-health",
    "otp-alert-candidates",
    "production-deployment",
    "deployed-telemetry-slo-query",
    "external-paging",
    "incident-response-execution",
    "rollback-execution",
    "cap123-portfolio-status",
}

ALLOWED_STATUSES = {
    "CI_VALIDATED",
    "DEPLOYMENT_UNCONFIGURED",
    "TELEMETRY_UNVERIFIED",
    "PAGING_UNVERIFIED",
    "OPERATOR_DRILL_PENDING",
    "PORTFOLIO_STATUS_STALE",
    "EXTERNALLY_VERIFIED",
}

ALLOWED_EVIDENCE = {
    "SOURCE_DEFINITION",
    "UNIT_TEST",
    "CI_WORKFLOW",
    "CAPABILITY_PORTFOLIO",
    "DEPLOYED_TELEMETRY_QUERY",
    "ALERT_DELIVERY_RECEIPT",
    "INCIDENT_TIMELINE",
    "HUMAN_OPERATOR_ATTESTATION",
    "ROLLBACK_EXECUTION_RECORD",
}

CI_EVIDENCE = {"SOURCE_DEFINITION", "UNIT_TEST", "CI_WORKFLOW"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Operational readiness evidence: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _items(contract: dict) -> dict[str, dict]:
    raw_items = contract.get("items")
    _require(isinstance(raw_items, list), "items must be a list")
    result: dict[str, dict] = {}
    for item in raw_items:
        _require(isinstance(item, dict), "item must be an object")
        item_id = item.get("item_id")
        _require(isinstance(item_id, str) and item_id, "item id")
        _require(item_id not in result, f"duplicate item id: {item_id}")
        result[item_id] = item
    return result


def _capability_row(capability_id: str) -> dict[str, str]:
    path = ROOT / "docs/roadmap/capability-portfolio.v1.tsv"
    with path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        for row in rows:
            if row["id"] == capability_id:
                return dict(row)
    raise SystemExit(
        f"Operational readiness evidence: FAIL — missing capability: {capability_id}"
    )


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-OPERATIONAL-READINESS-EVIDENCE-001",
        "contract id",
    )
    _require(contract["version"] == "1.0.0", "contract version")
    _require(contract["foundation_wave"] == "F4", "F4 binding")
    _require(contract["capabilities"] == ["CAP-123"], "CAP-123 binding")
    _require(
        contract["exit_criterion"]
        == "OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT",
        "F4 exit criterion binding",
    )

    policy = contract["policy"]
    for key in (
        "source_or_ci_is_deployed_observability",
        "aggregate_snapshot_is_slo_attainment",
        "alert_candidate_is_external_page_delivery",
        "acknowledgement_is_incident_resolution",
        "runbook_text_is_operator_execution",
    ):
        _require(policy[key] is False, f"false production claim policy: {key}")
    _require(
        policy["production_readiness_requires_external_evidence"] is True,
        "external evidence requirement",
    )
    _require(
        policy["capability_portfolio_status_must_match_evidence"] is True,
        "portfolio convergence requirement",
    )
    _require(set(contract["status_catalog"]) == ALLOWED_STATUSES, "status catalog")
    _require(set(contract["evidence_catalog"]) == ALLOWED_EVIDENCE, "evidence catalog")

    items = _items(contract)
    _require(set(items) == EXPECTED_ITEM_IDS, "complete readiness item set")

    expected_states = {
        "admin-operational-reports": "CI_VALIDATED",
        "otp-delivery-health": "CI_VALIDATED",
        "otp-alert-candidates": "CI_VALIDATED",
        "production-deployment": "DEPLOYMENT_UNCONFIGURED",
        "deployed-telemetry-slo-query": "TELEMETRY_UNVERIFIED",
        "external-paging": "PAGING_UNVERIFIED",
        "incident-response-execution": "OPERATOR_DRILL_PENDING",
        "rollback-execution": "OPERATOR_DRILL_PENDING",
        "cap123-portfolio-status": "PORTFOLIO_STATUS_STALE",
    }

    for item_id, item in items.items():
        _require(item["status"] in ALLOWED_STATUSES, f"invalid status: {item_id}")
        _require(item["status"] == expected_states[item_id], f"state drift: {item_id}")
        _require(
            isinstance(item.get("production_verified"), bool),
            f"production flag: {item_id}",
        )
        evidence_kinds = item.get("evidence_kinds")
        _require(
            isinstance(evidence_kinds, list) and evidence_kinds,
            f"evidence kinds: {item_id}",
        )
        _require(
            set(evidence_kinds).issubset(ALLOWED_EVIDENCE),
            f"unknown evidence kind: {item_id}",
        )
        sources = item.get("evidence_sources")
        _require(
            isinstance(sources, list) and sources,
            f"evidence sources: {item_id}",
        )
        for source in sources:
            _require(
                isinstance(source, str) and (ROOT / source).is_file(),
                f"missing evidence source for {item_id}: {source}",
            )
        _require(
            isinstance(item.get("next_required_proof"), str)
            and bool(item["next_required_proof"].strip()),
            f"next proof: {item_id}",
        )
        if item["status"] == "CI_VALIDATED":
            _require(
                set(evidence_kinds) == CI_EVIDENCE,
                f"CI evidence set: {item_id}",
            )
        if item["production_verified"] or item["status"] == "EXTERNALLY_VERIFIED":
            _require(
                item["production_verified"]
                and item["status"] == "EXTERNALLY_VERIFIED",
                f"external status convergence: {item_id}",
            )
            _require(
                not set(evidence_kinds).issubset(CI_EVIDENCE),
                f"CI-only production claim: {item_id}",
            )
        else:
            _require(
                item["status"] != "EXTERNALLY_VERIFIED",
                f"unverified external state: {item_id}",
            )

    requirements = contract["verification_requirements"]
    _require(
        requirements["deployed_telemetry_slo"] == ["DEPLOYED_TELEMETRY_QUERY"],
        "SLO evidence requirement",
    )
    _require(
        requirements["external_paging"] == ["ALERT_DELIVERY_RECEIPT"],
        "paging evidence requirement",
    )
    _require(
        set(requirements["incident_response"])
        == {"INCIDENT_TIMELINE", "HUMAN_OPERATOR_ATTESTATION"},
        "incident evidence requirement",
    )
    _require(
        set(requirements["rollback"])
        == {"ROLLBACK_EXECUTION_RECORD", "HUMAN_OPERATOR_ATTESTATION"},
        "rollback evidence requirement",
    )

    foundation = json.loads(_text("docs/contracts/foundation-completion-program.v1.json"))
    f4 = next(wave for wave in foundation["waves"] if wave["id"] == "F4")
    _require(
        "OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT" in f4["exit_criteria"],
        "foundation criterion",
    )
    _require(f4["status"] == "PENDING", "F4 must remain pending")

    portfolio = _capability_row("CAP-123")
    _require(portfolio["slug"] == "admin-operational-reports", "CAP-123 identity")
    _require(
        portfolio["status"] == "ROADMAP_ACCEPTED",
        "CAP-123 stale status must remain explicit until governance reconciliation",
    )

    admin_contract = json.loads(
        _text("docs/contracts/admin-operational-reports-snapshot.v1.json")
    )
    _require(
        admin_contract["capabilities"]["primary"] == ["CAP-123"],
        "Admin contract capability",
    )
    _require(
        admin_contract["cross_surface"]["repository_snapshot_is_deployed_observability"]
        is False,
        "Admin snapshot observability non-claim",
    )
    _require(
        admin_contract["cross_surface"]["repository_snapshot_is_slo_proof"] is False,
        "Admin snapshot SLO non-claim",
    )
    excluded = set(admin_contract["excluded"])
    for term in (
        "production_deployment",
        "deployed_slo_claim",
        "deployed_observability_claim",
        "incident_response_claim",
        "operator_rollback_claim",
        "production_readiness_claim",
    ):
        _require(term in excluded, f"Admin excluded claim: {term}")

    surface_contract = json.loads(
        _text("docs/contracts/surface-reachability-inventory.v1.json")
    )
    _require(
        surface_contract["policy"]["production_reachable_requires_external_evidence"]
        is True,
        "reachability external evidence policy",
    )
    _require(
        not any(surface["externally_reachable"] for surface in surface_contract["surfaces"]),
        "no production surface may already be externally verified",
    )

    admin_service = _text(
        "services/api/src/kefe_api/modules/admin_operational_reports/service.py"
    )
    admin_tests = _text("services/api/tests/test_admin_operational_reports_http.py")
    health_checker = _text("services/api/tools/check_otp_delivery_health_contract.py")
    alert_checker = _text(
        "services/api/tools/check_otp_delivery_alert_candidates_contract.py"
    )
    health_adr = _text("docs/adr/0114-durable-otp-delivery-health.md").lower()
    alert_adr = _text(
        "docs/adr/0116-durable-otp-alert-candidates-and-acknowledgement.md"
    ).lower()
    adr = _text("docs/adr/0119-operational-readiness-evidence-boundary.md")
    status = _text("docs/status/F4_OPERATIONAL_READINESS_EVIDENCE_2026-08-06.md")
    workflow = _text(".github/workflows/operational-readiness-evidence.yml")

    for fragment in (
        "class AdminOperationalReportsService",
        "def snapshot(",
        "def otp_delivery_alert_candidates(",
        "def acknowledge_otp_delivery_alert(",
    ):
        _require(fragment in admin_service, f"Admin service evidence: {fragment}")
    for fragment in (
        'body["aggregate_only"] is True',
        "test_signal_is_transparent_and_threshold_driven",
    ):
        _require(fragment in admin_tests, f"Admin test evidence: {fragment}")

    _require("OTP delivery health contract: PASS" in health_checker, "health checker")
    _require(
        "OTP delivery alert candidates contract: PASS" in alert_checker,
        "alert checker",
    )
    for phrase in ("provider acceptance is not deliverability", "telemetry completeness"):
        _require(phrase in health_adr, f"health non-claim: {phrase}")
    for phrase in (
        "external paging",
        "automated remediation",
        "operator response effectiveness",
    ):
        _require(phrase in alert_adr, f"alert non-claim: {phrase}")

    for phrase in (
        "A report snapshot is not an SLO result",
        "An internal alert candidate is not proof that a pager delivered anything",
        "A runbook or ADR is not evidence that an operator executed a drill",
    ):
        _require(phrase in adr, f"ADR boundary: {phrase}")
    for phrase in (
        "No deployed telemetry or SLO result is verified",
        "No external paging delivery is verified",
        "No incident or rollback execution is verified",
        "PORTFOLIO_STATUS_STALE",
    ):
        _require(phrase in status, f"status checkpoint: {phrase}")
    for fragment in (
        "Executable operational readiness evidence boundary",
        "Parent OTP delivery health contract",
        "Parent OTP alert candidate contract",
        "Targeted memory evidence",
        "Targeted PostgreSQL evidence",
        "No deployed telemetry, pager, incident or rollback proof",
    ):
        _require(fragment in workflow, f"workflow evidence: {fragment}")

    non_claims = contract["explicit_non_claims"]
    _require(isinstance(non_claims, list) and len(non_claims) >= 9, "non-claims")
    rendered_non_claims = " ".join(non_claims).lower()
    for phrase in (
        "production deployment",
        "deployed telemetry",
        "slo objective attainment",
        "external pager delivery",
        "incident-response exercise",
        "operator-executed rollback",
        "cap-123 portfolio reconciliation",
    ):
        _require(phrase in rendered_non_claims, f"missing non-claim: {phrase}")

    print(
        "Operational readiness evidence: PASS — source and CI foundations are "
        "distinguished from deployed telemetry, SLO, paging, incident and rollback "
        "proof; CAP-123 portfolio drift remains explicit and F4 remains pending."
    )


if __name__ == "__main__":
    main()

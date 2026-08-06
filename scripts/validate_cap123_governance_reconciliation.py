from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path(
    "docs/contracts/cap123-governance-reconciliation.v1.json"
)
PORTFOLIO_PATH = Path("docs/roadmap/capability-portfolio.v1.tsv")
PORTFOLIO_GOVERNANCE_PATH = Path("docs/roadmap/CAPABILITY_PORTFOLIO.md")
PORTFOLIO_VALIDATOR_PATH = Path("scripts/validate_capability_portfolio.py")
OPERATIONAL_READINESS_PATH = Path(
    "docs/contracts/operational-readiness-evidence.v1.json"
)
OPERATOR_DRILL_PATH = Path(
    "docs/contracts/operator-drill-evidence-protocol.v1.json"
)
ADR_PATH = Path("docs/adr/0121-cap123-governance-reconciliation.md")
STATUS_PATH = Path(
    "docs/status/F4_CAP123_GOVERNANCE_RECONCILIATION_2026-08-07.md"
)
WORKFLOW_PATH = Path(
    ".github/workflows/cap123-governance-reconciliation.yml"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(
            f"CAP-123 governance reconciliation: FAIL — {message}"
        )


def load_json(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    require(path.is_file(), f"missing file: {relative}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object required: {relative}")
    return value


def load_text(relative: Path) -> str:
    path = ROOT / relative
    require(path.is_file(), f"missing file: {relative}")
    return path.read_text(encoding="utf-8")


def portfolio_row() -> dict[str, str]:
    path = ROOT / PORTFOLIO_PATH
    require(path.is_file(), f"missing file: {PORTFOLIO_PATH}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    matches = [row for row in rows if row.get("id") == "CAP-123"]
    require(len(matches) == 1, "exactly one CAP-123 portfolio row")
    return matches[0]


def validate_contract(contract: dict[str, Any]) -> None:
    require(
        contract["contract_id"]
        == "KEFE-CAP123-GOVERNANCE-RECONCILIATION-001",
        "contract id",
    )
    require(contract["version"] == "1.0.0", "contract version")
    require(
        contract["status"] == "EVIDENCE_RECONCILIATION_ONLY",
        "reconciliation-only status",
    )
    require(contract["foundation_wave"] == "F4", "F4 binding")
    require(contract["capability_id"] == "CAP-123", "CAP-123 binding")
    require(
        contract["portfolio_path"] == str(PORTFOLIO_PATH),
        "portfolio path",
    )
    require(
        contract["portfolio_governance_path"]
        == str(PORTFOLIO_GOVERNANCE_PATH),
        "portfolio governance path",
    )

    authority = contract["owning_authority"]
    require(
        authority["product_register"]
        == "Product Bible Roadmap Capability Register",
        "product register authority",
    )
    require(
        authority["repository_authority_record"]
        == str(PORTFOLIO_GOVERNANCE_PATH),
        "repository authority record",
    )
    require(
        authority["owner_document_ids"] == ["KEFE-ADM-001", "KEFE-AED-001"],
        "owner document ids",
    )
    require(
        authority["repository_mirror_can_promote"] is False,
        "mirror promotion boundary",
    )

    current = contract["current_portfolio_state"]
    require(current["status"] == "ROADMAP_ACCEPTED", "current status")
    require(current["evidence"] == "", "current evidence mirror")
    require(current["source"] == "canonical", "canonical source")

    policy = contract["reconciliation_policy"]
    true_policies = {
        "repository_evidence_can_be_recorded",
        "ci_evidence_can_be_recorded",
        "explicit_owning_document_decision_required",
        "parent_stack_integration_required_before_status_change",
        "exact_head_ci_required_before_status_change",
    }
    false_policies = {
        "repository_evidence_is_deployed_evidence",
        "ci_evidence_is_production_evidence",
        "protocol_availability_is_human_execution",
        "automatic_portfolio_mutation_allowed",
        "mirror_can_create_product_decision",
    }
    for key in true_policies:
        require(policy[key] is True, f"required policy: {key}")
    for key in false_policies:
        require(policy[key] is False, f"false-claim policy: {key}")

    transition = contract["candidate_transition"]
    require(transition["from"] == "ROADMAP_ACCEPTED", "transition source")
    require(transition["to"] == "IMPLEMENTED_PARTIAL", "candidate status")
    require(
        transition["eligible_for_governance_review"] is True,
        "governance-review eligibility",
    )
    require(
        transition["performed_by_this_change"] is False,
        "no automatic transition",
    )
    require(
        "Product Bible" in transition["authority"],
        "owning-document authority",
    )

    verified = contract["implemented_verified_gate"]
    require(verified["status_allowed_now"] is False, "verified gate")
    require(
        {
            "approved_production_deployment_identity",
            "externally_observed_surface_reachability",
            "deployed_telemetry_query",
            "slo_and_error_budget_result",
            "external_pager_delivery_receipt",
            "human_incident_response_attestation",
            "human_rollback_execution_attestation",
            "explicit_owning_document_decision",
        }
        <= set(verified["required_evidence"]),
        "verified evidence requirements",
    )

    catalog = contract["evidence_catalog"]
    require(len(catalog) == 3, "evidence catalog")
    require(
        {item["evidence_id"] for item in catalog}
        == {
            "CAP123-REPOSITORY-RUNTIME",
            "CAP123-DELIVERY-OBSERVABILITY",
            "CAP123-OPERATIONAL-READINESS-BOUNDARY",
        },
        "evidence ids",
    )
    for item in catalog:
        require(item["verified_in_repository"] is True, "repository evidence")
        require(item["production_verified"] is False, "production boundary")
        require(item["human_verified"] is False, "human boundary")
        require(item["paths"], f"evidence paths: {item['evidence_id']}")
        for relative in item["paths"]:
            require((ROOT / relative).is_file(), f"missing evidence: {relative}")

    require(
        contract["stack_references"]
        == [
            "PR-323",
            "PR-325",
            "PR-327",
            "PR-329",
            "PR-331",
            "PR-333",
            "PR-335",
            "PR-338",
        ],
        "stack references",
    )
    require(
        set(contract["unresolved_gates"])
        == {
            "parent_stack_integration",
            "approved_production_deployment",
            "external_surface_reachability",
            "deployed_telemetry_and_slo_evidence",
            "external_pager_delivery_receipt",
            "human_incident_response_evidence",
            "human_rollback_evidence",
            "explicit_product_bible_lifecycle_decision",
        },
        "unresolved gates",
    )

    evidence = contract["current_evidence_state"]
    require(evidence["repository_runtime_present"] is True, "runtime evidence")
    require(evidence["ci_validation_present"] is True, "CI evidence")
    for key in (
        "production_deployment_verified",
        "external_reachability_verified",
        "deployed_telemetry_verified",
        "external_paging_verified",
        "human_incident_response_verified",
        "human_rollback_verified",
        "portfolio_lifecycle_promoted",
        "f4_complete",
    ):
        require(evidence[key] is False, f"unverified state: {key}")


def validate_portfolio(contract: dict[str, Any]) -> None:
    row = portfolio_row()
    require(row["slug"] == "admin-operational-reports", "portfolio slug")
    require(
        row["title"] == "Admin operational/trust/editorial reports",
        "portfolio title",
    )
    require(row["status"] == "ROADMAP_ACCEPTED", "portfolio status")
    require(row["evidence"] == "", "portfolio evidence remains unchanged")
    require(row["source"] == "canonical", "portfolio source")
    require(
        row["owners"].split("|")
        == contract["owning_authority"]["owner_document_ids"],
        "portfolio owner authority",
    )
    require(
        row["status"] == contract["current_portfolio_state"]["status"],
        "contract/portfolio status convergence",
    )

    governance = load_text(PORTFOLIO_GOVERNANCE_PATH).lower()
    for phrase in (
        "product bible roadmap capability register",
        "does not create or promote product decisions",
        "owning documents and explicit decisions",
    ):
        require(phrase in governance, f"portfolio governance: {phrase}")

    validator = load_text(PORTFOLIO_VALIDATOR_PATH)
    require("IMPLEMENTED_PARTIAL" in validator, "partial lifecycle catalog")
    require("IMPLEMENTED_VERIFIED" in validator, "verified lifecycle catalog")


def validate_parent_evidence() -> None:
    readiness = load_json(OPERATIONAL_READINESS_PATH)
    require(readiness["capabilities"] == ["CAP-123"], "parent capability")
    require(
        readiness["policy"]["capability_portfolio_status_must_match_evidence"]
        is True,
        "parent reconciliation policy",
    )
    items = {item["item_id"]: item for item in readiness["items"]}
    expected = {
        "cap123-portfolio-status": "PORTFOLIO_STATUS_STALE",
        "production-deployment": "DEPLOYMENT_UNCONFIGURED",
        "deployed-telemetry-slo-query": "TELEMETRY_UNVERIFIED",
        "external-paging": "PAGING_UNVERIFIED",
        "incident-response-execution": "OPERATOR_DRILL_PENDING",
        "rollback-execution": "OPERATOR_DRILL_PENDING",
    }
    for item_id, status in expected.items():
        require(items[item_id]["status"] == status, f"parent state: {item_id}")

    drills = load_json(OPERATOR_DRILL_PATH)
    current = drills["current_evidence"]
    require(current["accepted_record_ids"] == [], "accepted drill records")
    require(
        current["incident_response_status"] == "OPERATOR_DRILL_PENDING",
        "drill incident state",
    )
    require(
        current["rollback_status"] == "OPERATOR_DRILL_PENDING",
        "drill rollback state",
    )
    require(current["production_verified"] is False, "drill production state")


def validate_documents(contract: dict[str, Any]) -> None:
    adr = load_text(ADR_PATH)
    status = load_text(STATUS_PATH)
    workflow = load_text(WORKFLOW_PATH)
    for phrase in (
        "Evidence reconciliation is not lifecycle promotion",
        "The repository mirror cannot create a Product Bible decision",
        "IMPLEMENTED_PARTIAL is a candidate state, not an automatic transition",
    ):
        require(phrase in adr, f"ADR boundary: {phrase}")
    for phrase in (
        "CAP-123 remains `ROADMAP_ACCEPTED`",
        "No lifecycle promotion is performed",
        "F4 remains pending",
    ):
        require(phrase in status, f"status boundary: {phrase}")
    for phrase in (
        "Validate reconciliation JSON",
        "Executable CAP-123 reconciliation",
        "Existing capability portfolio gate",
        "Parent F4 evidence boundaries",
        "No product lifecycle promotion",
    ):
        require(phrase in workflow, f"workflow boundary: {phrase}")

    non_claims = " ".join(contract["explicit_non_claims"]).lower()
    for phrase in (
        "does not change the cap-123 portfolio status",
        "does not create or replace a product bible decision",
        "not production deployment evidence",
        "not human operator execution",
        "cap-123 is not implemented_verified",
        "f4 remains pending",
    ):
        require(phrase in non_claims, f"non-claim: {phrase}")


def main() -> None:
    contract = load_json(CONTRACT_PATH)
    validate_contract(contract)
    validate_portfolio(contract)
    validate_parent_evidence()
    validate_documents(contract)
    print(
        "CAP-123 governance reconciliation: PASS — repository and CI evidence "
        "is cataloged without changing ROADMAP_ACCEPTED; IMPLEMENTED_PARTIAL "
        "remains a governance candidate and IMPLEMENTED_VERIFIED is blocked."
    )


if __name__ == "__main__":
    main()

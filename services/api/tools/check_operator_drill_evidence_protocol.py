from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RECORDS = ROOT / "docs/evidence/operator-drills/records"
CLASSES = {
    "TEMPLATE_ONLY",
    "CI_SIMULATED",
    "HUMAN_ATTESTED_NON_PRODUCTION",
    "HUMAN_ATTESTED_PRODUCTION",
}
HUMAN = CLASSES - {"TEMPLATE_ONLY", "CI_SIMULATED"}
TYPES = {"INCIDENT_RESPONSE", "ROLLBACK_EXECUTION"}
ID_PATTERN = re.compile(r"^KEFE-(IR|RB)-[A-Z0-9][A-Z0-9_-]{5,63}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(
            f"Operator drill evidence protocol: FAIL — {message}"
        )


def load(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    require(path.is_file(), f"missing file: {relative}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object required: {relative}")
    return value


def text(relative: str) -> str:
    path = ROOT / relative
    require(path.is_file(), f"missing file: {relative}")
    return path.read_text(encoding="utf-8")


def utc(value: Any, label: str) -> datetime:
    require(isinstance(value, str) and value, f"{label} timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(
            f"Operator drill evidence protocol: FAIL — invalid {label}"
        ) from exc
    require(parsed.utcoffset() == timedelta(0), f"{label} must be UTC")
    return parsed


def reject_sensitive(
    value: Any,
    keys: set[str],
    fragments: tuple[str, ...],
    location: str = "$",
) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            require(
                key.lower() not in keys,
                f"forbidden sensitive key at {location}.{key}",
            )
            reject_sensitive(
                nested, keys, fragments, f"{location}.{key}"
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_sensitive(
                nested, keys, fragments, f"{location}[{index}]"
            )
    elif isinstance(value, str):
        lowered = value.lower()
        require(
            not any(item.lower() in lowered for item in fragments),
            f"forbidden sensitive value at {location}",
        )


def validate_timeline(
    record: dict[str, Any], required_phases: list[str]
) -> None:
    exercise = record["exercise"]
    start = utc(exercise["started_at"], "exercise start")
    end = utc(exercise["ended_at"], "exercise end")
    require(start < end, "exercise chronology")
    timeline = record["timeline"]
    require(isinstance(timeline, list) and timeline, "timeline")
    require(
        [event.get("sequence") for event in timeline]
        == list(range(1, len(timeline) + 1)),
        "timeline sequence",
    )
    phases: list[str] = []
    previous = start
    for event in timeline:
        require(
            set(event)
            == {
                "sequence",
                "phase",
                "occurred_at",
                "action",
                "observed_result",
            },
            "timeline event fields",
        )
        occurred = utc(event["occurred_at"], "timeline event")
        require(start <= occurred <= end, "timeline bounds")
        require(previous <= occurred, "timeline chronology")
        previous = occurred
        phases.append(event["phase"])
    cursor = 0
    for phase in required_phases:
        try:
            cursor = phases.index(phase, cursor) + 1
        except ValueError as exc:
            raise SystemExit(
                "Operator drill evidence protocol: FAIL — "
                f"missing or unordered phase: {phase}"
            ) from exc


def validate_template(
    record: dict[str, Any], record_type: str
) -> None:
    expected_id = (
        "KEFE-IR-TEMPLATE"
        if record_type == "INCIDENT_RESPONSE"
        else "KEFE-RB-TEMPLATE"
    )
    require(record["record_id"] == expected_id, "template id")
    require(record["record_type"] == record_type, "template type")
    require(record["classification"] == "TEMPLATE_ONLY", "template class")
    require(record["template"] is True, "template marker")
    require(record["environment"]["kind"] == "TEMPLATE", "template env")
    require(record["environment"]["approved"] is False, "template approval")
    require(record["timeline"] == [], "template timeline")
    require(record["artifacts"] == [], "template artifacts")
    require(record["actors"]["approver"] is None, "template approver")
    require(record["outcomes"]["result"] == "NOT_EXECUTED", "template result")
    require(record["attestation"]["method"] == "NONE", "template attestation")
    require(not any(record["claims"].values()), "template proof claim")


def actor(value: Any, label: str) -> dict[str, Any]:
    require(
        isinstance(value, dict)
        and set(value) == {"identity_provider", "subject_ref", "role"},
        f"{label} actor",
    )
    require(
        all(
            isinstance(value[key], str) and value[key].strip()
            for key in value
        ),
        f"{label} actor values",
    )
    return value


def validate_record(
    record: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    record_type = record["record_type"]
    classification = record["classification"]
    require(record_type in TYPES, "record type")
    require(classification in CLASSES - {"TEMPLATE_ONLY"}, "record class")
    require(record["template"] is False, "record template marker")
    require(
        isinstance(record["record_id"], str)
        and ID_PATTERN.fullmatch(record["record_id"]) is not None,
        "record id",
    )
    forbidden = contract["forbidden_content"]
    reject_sensitive(
        record,
        {key.lower() for key in forbidden["keys"]},
        tuple(forbidden["value_fragments"]),
    )
    validate_timeline(
        record, contract["required_timeline_phases"][record_type]
    )

    redaction = record["redaction"]
    require(redaction["reviewed"] is True, "redaction review")
    require(redaction["contains_secrets"] is False, "secret content")
    require(
        redaction["contains_raw_customer_data"] is False,
        "raw customer data",
    )

    operator = actor(record["actors"]["operator"], "operator")
    approver = record["actors"]["approver"]
    environment = record["environment"]
    attestation = record["attestation"]
    claims = record["claims"]
    relevant = (
        "incident_response_executed"
        if record_type == "INCIDENT_RESPONSE"
        else "rollback_executed"
    )
    unrelated = (
        "rollback_executed"
        if record_type == "INCIDENT_RESPONSE"
        else "incident_response_executed"
    )
    require(claims[unrelated] is False, "cross-type claim")

    if classification == "CI_SIMULATED":
        require(environment["kind"] == "CI", "CI environment")
        require(environment["approved"] is False, "CI approval")
        require(
            environment["deployment_identity"] is None,
            "CI deployment identity",
        )
        require(
            operator["identity_provider"] == "GITHUB_ACTIONS",
            "CI operator",
        )
        require(approver is None, "CI approver")
        require(attestation["method"] == "NONE", "CI attestation")
        require(
            attestation["operator_attested"] is False
            and attestation["approver_attested"] is False,
            "CI attestation flags",
        )
        require(not any(claims.values()), "CI proof claims")
        return

    require(classification in HUMAN, "human classification")
    expected_environment = (
        "PRODUCTION"
        if classification == "HUMAN_ATTESTED_PRODUCTION"
        else "NON_PRODUCTION"
    )
    require(
        environment["kind"] == expected_environment,
        "human environment/classification",
    )
    require(environment["approved"] is True, "approved environment")
    require(
        operator["identity_provider"]
        in {"ORGANIZATION_IDP", "TICKET_SYSTEM"},
        "operator identity provider",
    )
    approver = actor(approver, "approver")
    require(
        approver["identity_provider"]
        in {"ORGANIZATION_IDP", "TICKET_SYSTEM"},
        "approver identity provider",
    )
    require(
        operator["subject_ref"] != approver["subject_ref"],
        "independent approver",
    )
    require(record["artifacts"], "human artifact provenance")
    artifact_hashes: set[str] = set()
    for evidence in record["artifacts"]:
        require(
            isinstance(evidence["sha256"], str)
            and SHA256.fullmatch(evidence["sha256"]) is not None,
            "artifact sha256",
        )
        utc(evidence["captured_at"], "artifact capture")
        artifact_hashes.add(evidence["sha256"])

    require(
        record["outcomes"]["result"] != "NOT_EXECUTED",
        "human execution result",
    )
    require(
        attestation["operator_attested"] is True
        and attestation["approver_attested"] is True
        and attestation["method"] != "NONE",
        "human attestations",
    )
    utc(attestation["operator_signed_at"], "operator signature")
    utc(attestation["approver_signed_at"], "approver signature")
    require(claims[relevant] is True, "relevant execution claim")

    if classification == "HUMAN_ATTESTED_PRODUCTION":
        require(
            isinstance(environment["deployment_identity"], str)
            and environment["deployment_identity"].strip(),
            "production deployment identity",
        )
        require(claims["production_executed"] is True, "production claim")
    else:
        require(
            environment["deployment_identity"] is None,
            "non-production deployment identity",
        )
        require(claims["production_executed"] is False, "production claim")
        require(
            claims["rto_attained"] is False
            and claims["rpo_attained"] is False,
            "non-production recovery claim",
        )

    metrics = record["outcomes"]["recovery_metrics"]
    for prefix in ("rto", "rpo"):
        if claims[f"{prefix}_attained"]:
            objective = metrics[f"{prefix}_objective_seconds"]
            observed = metrics[f"{prefix}_observed_seconds"]
            require(
                isinstance(objective, int)
                and isinstance(observed, int)
                and observed <= objective,
                f"{prefix.upper()} metrics",
            )
            require(
                metrics["source_artifact_sha256"] in artifact_hashes,
                f"{prefix.upper()} artifact provenance",
            )


def derived_status(
    records: list[dict[str, Any]], record_type: str
) -> str:
    classes = {
        record["classification"]
        for record in records
        if record["record_type"] == record_type
    }
    if "HUMAN_ATTESTED_PRODUCTION" in classes:
        return "PRODUCTION_DRILL_VERIFIED"
    if "HUMAN_ATTESTED_NON_PRODUCTION" in classes:
        return "NON_PRODUCTION_DRILL_VERIFIED"
    return "OPERATOR_DRILL_PENDING"


def main() -> None:
    contract = load(
        "docs/contracts/operator-drill-evidence-protocol.v1.json"
    )
    schema = load(
        "docs/contracts/operator-drill-evidence-record.schema.v1.json"
    )
    require(
        contract["contract_id"]
        == "KEFE-OPERATOR-DRILL-EVIDENCE-PROTOCOL-001",
        "contract id",
    )
    require(contract["version"] == "1.0.0", "contract version")
    require(contract["status"] == "IMPLEMENTED_PROTOCOL_ONLY", "status")
    require(contract["foundation_wave"] == "F4", "F4 binding")
    require(contract["capabilities"] == ["CAP-123"], "CAP-123 binding")
    require(
        contract["exit_criterion"]
        == "OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT",
        "F4 criterion",
    )
    require(set(contract["classification_catalog"]) == CLASSES, "classes")
    require(set(contract["record_type_catalog"]) == TYPES, "record types")

    policy = contract["policy"]
    for key in (
        "template_is_execution_evidence",
        "ci_simulation_is_human_execution",
        "ci_can_create_human_attestation",
        "protocol_availability_is_production_readiness",
    ):
        require(policy[key] is False, f"false-claim policy: {key}")
    for key in (
        "human_attestation_requires_independent_approver",
        "production_claim_requires_approved_environment",
        "production_claim_requires_deployment_identity",
        "human_evidence_requires_artifact_provenance",
        "sensitive_data_is_forbidden",
        "missing_evidence_keeps_operator_state_pending",
    ):
        require(policy[key] is True, f"required policy: {key}")

    effects = contract["proof_effects"]
    require(set(effects) == CLASSES, "proof effects")
    for classification in ("TEMPLATE_ONLY", "CI_SIMULATED"):
        require(
            not any(effects[classification].values()),
            f"non-proof effect: {classification}",
        )
    require(
        effects["HUMAN_ATTESTED_NON_PRODUCTION"]
        == {
            "human_executed": True,
            "eligible_for_relevant_requirement": True,
            "production_verified": False,
        },
        "non-production proof effect",
    )
    require(
        all(effects["HUMAN_ATTESTED_PRODUCTION"].values()),
        "production proof effect",
    )

    require(
        schema["$schema"]
        == "https://json-schema.org/draft/2020-12/schema",
        "schema dialect",
    )
    require(
        schema["$id"]
        == "urn:kefe:contract:operator-drill-evidence-record:v1",
        "schema id",
    )
    require(schema["additionalProperties"] is False, "closed schema")
    require(
        set(schema["properties"]["classification"]["enum"]) == CLASSES,
        "schema classes",
    )
    require(
        set(schema["properties"]["record_type"]["enum"]) == TYPES,
        "schema record types",
    )

    expected_templates = {
        "INCIDENT_RESPONSE":
            "docs/evidence/operator-drills/templates/"
            "incident-response.template.json",
        "ROLLBACK_EXECUTION":
            "docs/evidence/operator-drills/templates/"
            "rollback-execution.template.json",
    }
    require(len(contract["templates"]) == 2, "template catalog")
    for item in contract["templates"]:
        record_type = item["record_type"]
        require(
            item["path"] == expected_templates[record_type]
            and item["classification"] == "TEMPLATE_ONLY"
            and item["proof"] is False,
            f"template entry: {record_type}",
        )
        validate_template(load(item["path"]), record_type)

    records: list[dict[str, Any]] = []
    ids: set[str] = set()
    if RECORDS.is_dir():
        for path in sorted(RECORDS.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            require(isinstance(record, dict), f"record object: {path.name}")
            validate_record(record, contract)
            require(record["record_id"] not in ids, "duplicate record id")
            ids.add(record["record_id"])
            records.append(record)

    current = contract["current_evidence"]
    accepted = sorted(
        record["record_id"]
        for record in records
        if record["classification"] in HUMAN
    )
    incident = derived_status(records, "INCIDENT_RESPONSE")
    rollback = derived_status(records, "ROLLBACK_EXECUTION")
    require(current["accepted_record_ids"] == accepted, "accepted records")
    require(current["incident_response_status"] == incident, "incident state")
    require(current["rollback_status"] == rollback, "rollback state")
    require(
        current["production_verified"]
        is (
            incident == "PRODUCTION_DRILL_VERIFIED"
            and rollback == "PRODUCTION_DRILL_VERIFIED"
        ),
        "production state",
    )

    parent = load("docs/contracts/operational-readiness-evidence.v1.json")
    require(
        parent["verification_requirements"]["incident_response"]
        == ["INCIDENT_TIMELINE", "HUMAN_OPERATOR_ATTESTATION"],
        "parent incident requirement",
    )
    require(
        parent["verification_requirements"]["rollback"]
        == ["ROLLBACK_EXECUTION_RECORD", "HUMAN_OPERATOR_ATTESTATION"],
        "parent rollback requirement",
    )
    parent_items = {item["item_id"]: item for item in parent["items"]}
    if incident == "OPERATOR_DRILL_PENDING":
        require(
            parent_items["incident-response-execution"]["status"]
            == "OPERATOR_DRILL_PENDING",
            "parent incident state",
        )
    if rollback == "OPERATOR_DRILL_PENDING":
        require(
            parent_items["rollback-execution"]["status"]
            == "OPERATOR_DRILL_PENDING",
            "parent rollback state",
        )

    adr = text(
        "docs/adr/0120-operator-drill-evidence-acceptance-protocol.md"
    )
    status = text(
        "docs/status/F4_OPERATOR_DRILL_EVIDENCE_PROTOCOL_2026-08-06.md"
    )
    workflow = text(
        ".github/workflows/operator-drill-evidence-protocol.yml"
    )
    for phrase in (
        "A template is not an executed drill",
        "CI cannot create a human attestation",
        "Independent approval is required",
    ):
        require(phrase in adr, f"ADR boundary: {phrase}")
    for phrase in (
        "OPERATOR_DRILL_PENDING",
        "No incident-response exercise has been executed",
        "No rollback has been executed",
    ):
        require(phrase in status, f"status boundary: {phrase}")
    for phrase in (
        "Validate protocol JSON",
        "Executable evidence acceptance protocol",
        "Parent operational readiness evidence boundary",
        "No human or production drill executed",
    ):
        require(phrase in workflow, f"workflow boundary: {phrase}")

    non_claims = " ".join(contract["explicit_non_claims"]).lower()
    for phrase in (
        "no incident-response exercise",
        "no rollback",
        "templates are not execution evidence",
        "ci validation is not human operator attestation",
        "no production deployment",
        "no production slo",
        "f4 remains pending",
    ):
        require(phrase in non_claims, f"non-claim: {phrase}")

    print(
        "Operator drill evidence protocol: PASS — templates and CI simulations "
        "cannot become human or production proof; human records require "
        "independent attestation, provenance and privacy-safe content. "
        f"Current states: incident={incident}, rollback={rollback}."
    )


if __name__ == "__main__":
    main()

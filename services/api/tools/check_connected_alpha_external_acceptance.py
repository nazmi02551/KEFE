from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/connected-alpha-external-acceptance.v1.json"
TOOL = ROOT / "services/api/tools/run_connected_alpha_acceptance.py"
PRIVACY_ROUTER = ROOT / "services/api/src/kefe_api/modules/privacy/router.py"
PRIVACY_SERVICE = ROOT / "services/api/src/kefe_api/modules/privacy/service.py"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden behavior: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-CONNECTED-ALPHA-EXTERNAL-ACCEPTANCE-001":
        raise SystemExit("unexpected external acceptance contract id")
    if contract["preconditions"]["explicit_allow_write_required"] is not True:
        raise SystemExit("remote write acceptance must be explicit")
    if contract["preconditions"]["exact_deployed_source_commit_required"] is not True:
        raise SystemExit("deployed source identity must be exact")
    if contract["evidence_record"]["source_commit_pattern"] != "^[0-9a-f]{40}$":
        raise SystemExit("evidence source commit must be an exact 40-hex SHA")
    if contract["write_scope"]["exact_guest_count"] != 2:
        raise SystemExit("acceptance must remain exactly two-actor")
    if contract["write_scope"]["privacy_cleanup_required"] is not True:
        raise SystemExit("acceptance actors must be cleaned through privacy self-service")
    external_ci_allowed = contract["execution_authority"][
        "ci_may_execute_against_real_endpoint_automatically"
    ]
    if external_ci_allowed is not False:
        raise SystemExit("CI must not automatically mutate an external alpha deployment")

    tool = TOOL.read_text(encoding="utf-8")
    privacy_router = PRIVACY_ROUTER.read_text(encoding="utf-8")
    privacy_service = PRIVACY_SERVICE.read_text(encoding="utf-8")

    for needle in (
        'parsed.scheme.lower() != "https"',
        'hostname.endswith(".invalid")',
        '_EXACT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")',
        '_validate_source_commit(source_commit)',
        'if not allow_write:',
        'client.request("GET", "/health")',
        'client.request("GET", "/ready")',
        '"/v1/identity/guest"',
        "options[0]",
        "options[1]",
        'result.get("layer") != "RAW"',
        'after_second["n"] != after_first["n"] + 1',
        'reread_first["n"] != after_second["n"]',
        'reread_first["result"] != after_second["result"]',
        '"DELETE"',
        '"/v1/me"',
        '"X-KEFE-Delete-Confirm": f"DELETE:{actor.actor_id}"',
        'for actor in reversed(actors):',
        '"status": "ACCEPTED_PENDING_CLEANUP"',
        'record["status"] = "ACCEPTED_CLEANED"',
        'raise AcceptanceError("unexpected acceptance failure") from primary_error',
    ):
        require(tool, needle, where="acceptance tool")

    for forbidden in (
        "ssl._create_unverified_context",
        "CERT_NONE",
        "private_reason",
        "demograph",
        "confidence_answer",
        'default=os.getenv("GITHUB_SHA", "unknown")',
        "access_token\":",
        "actor_id\": actor.actor_id",
    ):
        forbid(tool.lower(), forbidden.lower(), where="acceptance tool")

    require(
        privacy_router,
        'Header(alias="X-KEFE-Delete-Confirm")',
        where="privacy router",
    )
    require(
        privacy_service,
        'expected = f"DELETE:{principal.actor_id}"',
        where="privacy service",
    )

    print("Connected Alpha external acceptance contract: OK")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/surface-reachability-inventory.v1.json"

EXPECTED_SURFACE_IDS = {
    "canonical-api-local",
    "canonical-api-production",
    "admin-studio-local",
    "admin-studio-production",
    "consumer-web-production",
    "mobile-production-shell",
    "installable-phone-preview",
    "mobile-deeplinks",
    "web-deeplinks",
    "otp-provider-receipt-callback",
}

ALLOWED_STATUSES = {
    "REACHABLE_VERIFIED",
    "CI_ARTIFACT_AVAILABLE",
    "LOCAL_ONLY",
    "COMPILE_ONLY",
    "PLACEHOLDER_ONLY",
    "INTERNAL_ONLY",
    "NOT_CONFIGURED",
    "VERIFICATION_PENDING",
}

EXTERNAL_EVIDENCE = {
    "EXTERNAL_HTTP_PROBE",
    "STORE_DISTRIBUTION",
    "HUMAN_OPERATOR_ATTESTATION",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Surface reachability inventory: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _surface_map(contract: dict) -> dict[str, dict]:
    surfaces = contract.get("surfaces")
    _require(isinstance(surfaces, list), "surfaces must be a list")
    mapped: dict[str, dict] = {}
    for surface in surfaces:
        _require(isinstance(surface, dict), "surface entry must be an object")
        surface_id = surface.get("surface_id")
        _require(isinstance(surface_id, str) and surface_id, "surface id")
        _require(surface_id not in mapped, f"duplicate surface id: {surface_id}")
        mapped[surface_id] = surface
    return mapped


def _is_forbidden_endpoint(endpoint: str, patterns: list[str]) -> bool:
    lowered = endpoint.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-SURFACE-REACHABILITY-INVENTORY-001",
        "contract id",
    )
    _require(contract["version"] == "1.0.0", "contract version")
    _require(contract["wave"] == "F4", "F4 binding")
    _require(
        contract["capabilities"] == ["CAP-092", "CAP-123"],
        "capability binding",
    )
    _require(
        contract["exit_criterion"]
        == "PRODUCTION_AND_PREVIEW_SURFACE_REACHABILITY_INVENTORIED",
        "F4 exit criterion binding",
    )

    policy = contract["policy"]
    _require(policy["inventory_is_deployment_evidence"] is False, "inventory claim")
    _require(
        policy["ci_build_is_external_reachability_evidence"] is False,
        "CI build claim",
    )
    _require(
        policy["local_probe_is_external_reachability_evidence"] is False,
        "local probe claim",
    )
    _require(
        policy["production_reachable_requires_external_evidence"] is True,
        "external evidence requirement",
    )
    _require(
        set(policy["external_evidence_kinds"]) == EXTERNAL_EVIDENCE,
        "external evidence catalog",
    )
    forbidden_patterns = policy["forbidden_production_endpoint_patterns"]
    _require(
        set(forbidden_patterns)
        == {".invalid", "localhost", "127.0.0.1", "0.0.0.0", "10.0.2.2"},
        "forbidden production endpoint patterns",
    )
    _require(set(contract["status_catalog"]) == ALLOWED_STATUSES, "status catalog")

    surfaces = _surface_map(contract)
    _require(set(surfaces) == EXPECTED_SURFACE_IDS, "complete canonical surface set")

    for surface_id, surface in surfaces.items():
        status = surface.get("status")
        _require(status in ALLOWED_STATUSES, f"invalid status: {surface_id}")
        _require(
            isinstance(surface.get("externally_reachable"), bool),
            f"external reachability flag: {surface_id}",
        )
        _require(
            surface.get("evidence_kind") in contract["evidence_catalog"],
            f"evidence kind: {surface_id}",
        )
        sources = surface.get("evidence_sources")
        _require(
            isinstance(sources, list) and sources,
            f"evidence sources: {surface_id}",
        )
        for source in sources:
            _require(
                isinstance(source, str) and (ROOT / source).is_file(),
                f"missing evidence source for {surface_id}: {source}",
            )
        _require(
            isinstance(surface.get("next_required_proof"), str)
            and bool(surface["next_required_proof"].strip()),
            f"next proof: {surface_id}",
        )

        externally_reachable = surface["externally_reachable"]
        if externally_reachable or status == "REACHABLE_VERIFIED":
            _require(
                externally_reachable and status == "REACHABLE_VERIFIED",
                f"reachable status/flag convergence: {surface_id}",
            )
            _require(
                surface["evidence_kind"] in EXTERNAL_EVIDENCE,
                f"external evidence required: {surface_id}",
            )
            endpoint = surface.get("endpoint")
            if surface["evidence_kind"] == "EXTERNAL_HTTP_PROBE":
                _require(isinstance(endpoint, str), f"HTTPS endpoint: {surface_id}")
                parsed = urlsplit(endpoint)
                _require(
                    parsed.scheme == "https" and bool(parsed.netloc),
                    f"production HTTPS endpoint: {surface_id}",
                )
                _require(
                    not _is_forbidden_endpoint(endpoint, forbidden_patterns),
                    f"forbidden endpoint marked reachable: {surface_id}",
                )
        else:
            _require(
                status != "REACHABLE_VERIFIED",
                f"unverified reachable state: {surface_id}",
            )

    expected_states = {
        "canonical-api-local": ("LOCAL_ONLY", "LOCAL_RUNTIME", False),
        "canonical-api-production": ("NOT_CONFIGURED", "STATIC_CONFIG", False),
        "admin-studio-local": ("LOCAL_ONLY", "LOCAL_RUNTIME", False),
        "admin-studio-production": ("NOT_CONFIGURED", "STATIC_CONFIG", False),
        "consumer-web-production": ("PLACEHOLDER_ONLY", "STATIC_CONFIG", False),
        "mobile-production-shell": ("COMPILE_ONLY", "CI_BUILD_ARTIFACT", False),
        "installable-phone-preview": (
            "CI_ARTIFACT_AVAILABLE",
            "CI_BUILD_ARTIFACT",
            False,
        ),
        "mobile-deeplinks": ("NOT_CONFIGURED", "STATIC_CONFIG", False),
        "web-deeplinks": ("NOT_CONFIGURED", "STATIC_CONFIG", False),
        "otp-provider-receipt-callback": ("INTERNAL_ONLY", "STATIC_CONFIG", False),
    }
    for surface_id, expected in expected_states.items():
        actual = surfaces[surface_id]
        _require(
            (actual["status"], actual["evidence_kind"], actual["externally_reachable"])
            == expected,
            f"current state drift: {surface_id}",
        )

    mobile_main = _text("apps/mobile/lib/main.dart")
    mobile_config = _text("apps/mobile/lib/core/config/app_config.dart")
    mobile_pubspec = _text("apps/mobile/pubspec.yaml")
    mobile_readme = _text("apps/mobile/README.md")
    admin_env = _text("apps/admin/.env.example")
    admin_readme = _text("apps/admin/README.md")
    web_readme = _text("apps/web/README.md")
    installable_contract = json.loads(
        _text("docs/contracts/installable-phone-preview-hotfix.v1.json")
    )
    global_workflow = _text(".github/workflows/global-readiness.yml")
    callback_router = _text(
        "services/api/src/kefe_api/modules/identity/otp_provider_receipts_router.py"
    )
    callback_contract = _text("docs/contracts/otp-provider-receipts.v1.json")
    adr = _text(
        "docs/adr/0118-production-and-preview-surface-reachability-inventory.md"
    )
    status_doc = _text(
        "docs/status/F4_SURFACE_REACHABILITY_INVENTORY_2026-08-06.md"
    )
    workflow = _text(".github/workflows/surface-reachability-inventory.yml")

    _require(
        "https://beta-api.invalid/" in mobile_main,
        "production mobile placeholder endpoint",
    )
    _require("http://localhost:8000" in mobile_config, "mobile local API default")
    _require("http://localhost:8000" in admin_env, "Admin local API default")
    _require("production deployment" in admin_readme.lower(), "Admin non-claim")
    _require("public/deep-link/web experience" in web_readme, "web placeholder intent")
    web_entries = sorted(path.name for path in (ROOT / "apps/web").iterdir())
    _require(web_entries == ["README.md"], "consumer web must remain placeholder-only")

    _require("go_router:" in mobile_pubspec, "mobile route library")
    for forbidden_dependency in ("app_links:", "uni_links:", "firebase_dynamic_links:"):
        _require(
            forbidden_dependency not in mobile_pubspec,
            f"unexpected deeplink dependency without inventory update: {forbidden_dependency}",
        )
    _require(not (ROOT / "apps/mobile/android").exists(), "committed Android host")
    _require(not (ROOT / "apps/mobile/ios").exists(), "committed iOS host")
    _require("deep link" not in mobile_readme.lower(), "undeclared mobile deeplinks")

    production_entry = installable_contract["production_entry"]
    preview = installable_contract["installable_phone_preview"]
    _require(
        production_entry["placeholder_endpoint"] == "https://beta-api.invalid/",
        "phone contract placeholder endpoint",
    )
    _require(production_entry["apk_uploaded"] is False, "production APK non-claim")
    _require(
        preview["workflow_artifact_name"] == "kefe-installable-phone-preview",
        "phone preview artifact identity",
    )
    for fragment in (
        "Generate transient Android host",
        "Build installable phone preview",
        "name: kefe-installable-phone-preview",
        "flutter build apk --debug -t lib/main_preview.dart",
    ):
        _require(fragment in global_workflow, f"phone CI artifact evidence: {fragment}")

    for fragment in (
        '"/otp-delivery-receipts"',
        "include_in_schema=False",
    ):
        _require(fragment in callback_router, f"internal callback boundary: {fragment}")
    _require("openapi_exposed" in callback_contract, "callback OpenAPI non-exposure")

    for phrase in (
        "A GitHub Actions APK artifact is not a public release",
        "A compiled production shell is not a reachable mobile product",
        "A local URL is not a production endpoint",
    ):
        _require(phrase in adr, f"ADR non-claim: {phrase}")

    for phrase in (
        "No production surface is externally verified",
        "CI_ARTIFACT_AVAILABLE",
        "PRODUCTION_AND_PREVIEW_SURFACE_REACHABILITY_INVENTORIED",
    ):
        _require(phrase in status_doc, f"status checkpoint: {phrase}")

    for fragment in (
        "Executable surface reachability inventory",
        "Phone artifact boundary parent contract",
        "Production copy boundary parent contract",
        "OTP provider receipt parent contract",
        "No external reachability probe",
    ):
        _require(fragment in workflow, f"workflow evidence: {fragment}")

    non_claims = contract["explicit_non_claims"]
    _require(isinstance(non_claims, list) and len(non_claims) >= 8, "explicit non-claims")
    combined_non_claims = " ".join(non_claims).lower()
    for phrase in (
        "production api",
        "consumer web",
        "admin studio",
        "app link",
        "github actions artifact",
        "otp provider callback",
        "slo",
        "rollback",
    ):
        _require(phrase in combined_non_claims, f"missing non-claim: {phrase}")

    print(
        "Surface reachability inventory: PASS — production, local, preview, "
        "deeplink and internal callback surfaces are explicitly classified; CI/local "
        "evidence cannot masquerade as external reachability; placeholder and local "
        "endpoints remain fail-closed for production claims."
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/production-api-runtime.v1.json"
REACHABILITY = ROOT / "docs/contracts/surface-reachability-inventory.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Production API runtime: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-PRODUCTION-API-RUNTIME-001",
        "contract id",
    )
    _require(contract["version"] == "1.0.0", "contract version")
    _require(contract["wave"] == "F4", "F4 binding")
    _require(
        contract["capabilities"] == ["CAP-092", "CAP-123"],
        "capability binding",
    )

    runtime = contract["canonical_runtime"]
    _require(runtime["framework"] == "FastAPI", "canonical framework")
    _require(runtime["persistence"] == "PostgreSQL", "canonical persistence")
    _require(runtime["application"] == "kefe_api.main:app", "canonical application")
    _require(runtime["container_path"] == "services/api/Dockerfile", "container path")
    _require(runtime["container_port"] == 8000, "container port")
    _require(runtime["provider_neutral"] is True, "provider-neutral runtime")

    topology = contract["initial_connected_alpha_topology"]
    _require(topology["api_replica_count"] == 1, "initial replica count")
    _require(topology["horizontal_scaling_allowed"] is False, "scaling guard")
    _require(
        "guest admission" in topology["reason"].lower(),
        "process-local guest admission reason",
    )
    _require(
        topology["runbook"] == "docs/runbooks/CONNECTED_ALPHA_API_DEPLOYMENT.md",
        "deployment runbook binding",
    )

    config = contract["production_configuration"]
    _require(config["environment_value"] == "production", "production environment")
    _require(
        config["required_persistence_backend"] == "postgres",
        "postgres production",
    )
    _require(config["database_url_required"] is True, "database URL requirement")
    _require(config["database_scheme_prefix"] == "postgresql", "database scheme")
    _require(
        set(config["forbidden_database_hosts"])
        == {"localhost", "127.0.0.1", "0.0.0.0", "10.0.2.2"},
        "forbidden database hosts",
    )
    _require(
        config["forbidden_database_host_suffixes"] == [".invalid"],
        "reserved host suffix",
    )
    _require(
        config["development_merge_secret_forbidden"] is True,
        "development secret guard",
    )
    _require(config["otp_capture_forbidden"] is True, "OTP capture guard")
    _require(
        config["otp_abuse_guard_off_forbidden"] is True,
        "OTP abuse guard",
    )
    _require(config["committed_credentials_allowed"] is False, "credential policy")

    release = contract["schema_release"]
    _require(
        release["migration_command"] == "alembic upgrade head",
        "migration command",
    )
    _require(release["mode"] == "EXPLICIT_PRE_DEPLOY", "migration mode")
    _require(
        release["auto_migrate_on_api_startup"] is False,
        "no auto migration",
    )

    health = contract["health"]
    _require(health["liveness_path"] == "/health", "liveness path")
    _require(health["readiness_path"] == "/ready", "readiness path")
    _require(
        health["readiness_public_openapi"] is False,
        "readiness OpenAPI boundary",
    )
    _require(health["postgres_readiness_query"] == "SELECT 1", "readiness query")
    _require(health["failure_status"] == 503, "readiness status")
    _require(
        health["dependency_error_details_exposed"] is False,
        "readiness secret boundary",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    for fragment in (
        'self.persistence_backend != "postgres"',
        'not database.scheme.startswith("postgresql")',
        'hostname.endswith(".invalid")',
        'self.otp_delivery_mode == "CAPTURE"',
        'self.otp_request_guard_mode == "OFF"',
        "DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET",
    ):
        _require(fragment in settings, f"production settings guard: {fragment}")

    dockerfile = _text("services/api/Dockerfile")
    _require("FROM python:3.12-slim" in dockerfile, "Python 3.12 container")
    _require("kefe_api.main:app" in dockerfile, "canonical container app")
    _require('"--port", "8000"' in dockerfile, "container port command")
    _require(
        "alembic upgrade head" not in dockerfile,
        "no auto migration in API startup",
    )
    _require("forwarded-allow-ips=*" not in dockerfile, "no wildcard proxy trust")
    for forbidden in ("render.com", "railway", "supabase", "firebase", "neon.tech"):
        _require(
            forbidden not in dockerfile.lower(),
            f"provider lock in Dockerfile: {forbidden}",
        )

    readiness = _text("services/api/src/kefe_api/infrastructure/readiness.py")
    _require('text("SELECT 1")' in readiness, "PostgreSQL readiness query")
    _require("engine.connect()" in readiness, "readiness connection probe")

    health_router = _text("services/api/src/kefe_api/modules/health/router.py")
    _require('@router.get("/health"' in health_router, "liveness route")
    _require('@router.get("/ready"' in health_router, "readiness route")
    _require("include_in_schema=False" in health_router, "internal readiness route")
    _require('detail="not ready"' in health_router, "generic readiness failure")

    reachability = json.loads(REACHABILITY.read_text(encoding="utf-8"))
    production_api = next(
        surface
        for surface in reachability["surfaces"]
        if surface["surface_id"] == "canonical-api-production"
    )
    _require(
        production_api["status"]
        == contract["reachability_policy"]["current_inventory_status"],
        "reachability inventory must remain NOT_CONFIGURED before deployment",
    )
    _require(
        production_api["externally_reachable"] is False,
        "no external reachability claim",
    )

    guards = contract["architecture_guards"]
    _require(guards["parallel_backend_allowed"] is False, "no parallel backend")
    _require(
        guards["hosting_vendor_in_domain_code_allowed"] is False,
        "no vendor in domain",
    )
    _require(
        guards["preview_data_as_production_fallback_allowed"] is False,
        "preview isolation",
    )
    _require(guards["commit_first_preserved"] is True, "Commit First")
    _require(guards["blind_first_preserved"] is True, "Blind First")
    _require(
        guards["immutable_published_case_version_preserved"] is True,
        "immutable CaseVersion",
    )
    _require(guards["generic_flow_runtime_preserved"] is True, "generic Flow runtime")
    _require(guards["my_kefe_inference_allowed"] is False, "My KEFE non-inference")

    adr = _text("docs/adr/0122-provider-neutral-production-api-runtime-boundary.md")
    _require("No Supabase, Firebase, alternate API" in adr, "canonical backend ADR")
    _require(
        "does not make the API externally reachable" in adr,
        "reachability non-claim",
    )
    _require("CAP-123 lifecycle status" in adr, "governance non-promotion")

    runbook = _text("docs/runbooks/CONNECTED_ALPHA_API_DEPLOYMENT.md")
    _require("one API replica" in runbook, "single-replica initial topology")
    _require("alembic upgrade head" in runbook, "explicit migration runbook")
    _require("NOT_CONFIGURED" in runbook, "reachability non-claim runbook")
    _require("Product Preview" in runbook, "preview rollback prohibition")

    print("Production API runtime: PASS")


if __name__ == "__main__":
    main()

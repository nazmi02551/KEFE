from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "reviewed-proposal-source-slice33.v1.json"
)
MODULE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "ingestion_orchestration"
)
SOURCE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "editorial_projection"
    / "ingestion_source.py"
)
SECURED = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "editorial_projection.py"
)
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_ingestion_orchestration.py"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0020_reviewed_proposals.py"
)
ADMIN_MODELS = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "models.py"
)
ADMIN_POLICY = ADMIN_MODELS.with_name("policy.py")
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"


def _missing(content: str, fragments: tuple[str, ...], label: str) -> list[str]:
    return [f"{label} missing: {fragment}" for fragment in fragments if fragment not in content]


def main() -> int:
    required = (
        CONTRACT,
        MODULE / "models.py",
        MODULE / "ports.py",
        MODULE / "in_memory.py",
        MODULE / "service.py",
        SOURCE,
        SECURED,
        POSTGRES,
        MIGRATION,
        ADMIN_MODELS,
        ADMIN_POLICY,
        MAIN,
    )
    errors = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in required
        if not path.exists()
    ]
    if errors:
        print("\n".join(errors))
        return 1

    contract = CONTRACT.read_text(encoding="utf-8")
    models = (MODULE / "models.py").read_text(encoding="utf-8")
    ports = (MODULE / "ports.py").read_text(encoding="utf-8")
    repository = POSTGRES.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    secured = SECURED.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    admin_models = ADMIN_MODELS.read_text(encoding="utf-8")
    admin_policy = ADMIN_POLICY.read_text(encoding="utf-8")
    app = MAIN.read_text(encoding="utf-8")

    errors.extend(
        _missing(
            contract,
            (
                '"provider_neutral": true',
                '"proposal_payload_immutable_and_hashed": true',
                '"one_terminal_review_per_proposal": true',
                '"dedicated_capability": "CONTENT_PROJECT"',
                '"request_supplied_actor_forbidden": true',
                '"http_route_in_scope": false',
            ),
            "slice contract",
        )
    )
    errors.extend(
        _missing(
            models,
            (
                "class IngestionRun:",
                "class StageExecution:",
                "class Proposal:",
                "class ProposalReviewDecision:",
                "def stable_payload_hash(",
            ),
            "ingestion domain",
        )
    )
    errors.extend(
        _missing(
            ports,
            (
                "class IngestionOrchestrationRepository(Protocol):",
                "class StageProcessor(Protocol):",
                "def add_review_decision(",
            ),
            "ingestion ports",
        )
    )
    errors.extend(
        _missing(
            source,
            (
                "class IngestionReviewedProposalSource:",
                'candidate.payload.get("dependency_proposal_ids", [])',
                "get_review_decision(candidate_proposal_id)",
            ),
            "projection source adapter",
        )
    )
    errors.extend(
        _missing(
            secured,
            (
                "class SecuredEditorialProjectionService:",
                "AdminCapability.CONTENT_PROJECT",
                "requested_by_admin_ref=principal.audit_actor_ref",
            ),
            "secured projection facade",
        )
    )
    errors.extend(
        _missing(
            admin_models + admin_policy,
            (
                'CONTENT_PROJECT = "CONTENT_PROJECT"',
                "AdminCapability.CONTENT_PROJECT",
            ),
            "Admin capability policy",
        )
    )
    errors.extend(
        _missing(
            migration,
            (
                'revision = "20260802_0020"',
                'down_revision = "20260802_0019"',
                "CREATE TABLE ingestion.ingestion_run",
                "CREATE TABLE ingestion.stage_execution",
                "CREATE TABLE ingestion.proposal",
                "CREATE TABLE ingestion.proposal_review_decision",
                "proposal_id uuid NOT NULL UNIQUE",
            ),
            "migration",
        )
    )
    errors.extend(
        _missing(
            repository,
            (
                "ON CONFLICT (run_key) DO NOTHING",
                "INSERT INTO ingestion.stage_execution",
                "INSERT INTO ingestion.proposal",
                "INSERT INTO ingestion.proposal_review_decision",
            ),
            "PostgreSQL repository",
        )
    )
    errors.extend(
        _missing(
            app,
            (
                "build_editorial_pipeline",
                "app.state.ingestion_orchestration_service",
                "app.state.secured_editorial_projection_service",
            ),
            "application composition",
        )
    )

    combined = "\n".join(path.read_text(encoding="utf-8") for path in required)
    forbidden = (
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "@router.",
        ".publish(",
        ".approve(",
        ".submit_for_review(",
    )
    leaked = [fragment for fragment in forbidden if fragment in combined]
    if leaked:
        errors.append("forbidden provider/HTTP/lifecycle dependency: " + ", ".join(leaked))

    if errors:
        print("Reviewed Proposal source contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Reviewed Proposal source contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "ingestion-orchestration.v1.yaml"
ADR = (
    REPO_ROOT
    / "docs"
    / "adr"
    / "0028-provider-neutral-ingestion-orchestration-reviewed-proposals.md"
)
PACKAGE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "ingestion_orchestration"
)
MODELS = PACKAGE / "models.py"
PORTS = PACKAGE / "ports.py"
SERVICE = PACKAGE / "service.py"
MATERIALIZER = PACKAGE / "knowledge_materializer.py"
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260729_0016_ingestion_orchestration.py"
)
CONTEXT_MODELS = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "context" / "models.py"
)


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [f"{label} missing: {fragment}" for fragment in fragments if fragment not in content]


def main() -> int:
    errors: list[str] = []
    required_files = (
        CONTRACT,
        ADR,
        MODELS,
        PORTS,
        SERVICE,
        MATERIALIZER,
        MIGRATION,
        CONTEXT_MODELS,
    )
    for path in required_files:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = CONTRACT.read_text(encoding="utf-8")
    models = MODELS.read_text(encoding="utf-8")
    ports = PORTS.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    materializer = MATERIALIZER.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    context_models = CONTEXT_MODELS.read_text(encoding="utf-8")

    errors.extend(
        _require(
            contract,
            (
                "provider_specific_logic_ends_at_source_adapter: true",
                "ai_output_is_proposal_not_acceptance: true",
                "review_decision_is_separate_from_proposal: true",
                "accepted_materialization_must_be_idempotent: true",
                "bounded_retry_required: true",
                "accepted_candidate_case_creates_authoring_draft_in_this_contract: false",
                "direct_publish_call_from_orchestration_forbidden: true",
                "ai_or_provider_outage_must_not_break_consumer_core: true",
                "context_four_state_claim_projection_unchanged: true",
                "graph_database_added: false",
            ),
            label="orchestration contract",
        )
    )
    errors.extend(
        _require(
            models,
            (
                "class IngestionRun:",
                "class StageExecution:",
                "class Proposal:",
                "class ProposalReviewDecision:",
                "class ProposalMaterialization:",
                "FAILED_RETRYABLE",
                "FAILED_FINAL",
                "build_run_key(",
            ),
            label="orchestration domain",
        )
    )
    errors.extend(
        _require(
            ports,
            (
                "class IngestionOrchestrationRepository(Protocol):",
                "class StageProcessor(Protocol):",
                "class ProposalTargetMaterializer(Protocol):",
            ),
            label="orchestration ports",
        )
    )
    errors.extend(
        _require(
            service,
            (
                "class IngestionOrchestrationService:",
                "class RetryableStageError",
                "max_attempts",
                "ProposalReviewDecisionKind.ACCEPTED",
                "find_materialization(proposal_id)",
            ),
            label="orchestration service",
        )
    )
    errors.extend(
        _require(
            materializer,
            (
                '"CLAIM": self._claim',
                '"CLAIM_ASSESSMENT": self._claim_assessment',
                '"EVIDENCE_LINK": self._evidence_link',
                '"ARGUMENT": self._argument',
                "uuid5(NAMESPACE_URL",
                "review.reviewer_ref",
                "self._knowledge.list_claim_assessments",
            ),
            label="knowledge materializer",
        )
    )
    errors.extend(
        _require(
            migration,
            (
                "CREATE SCHEMA IF NOT EXISTS ingestion",
                "CREATE TABLE ingestion.ingestion_run",
                "CREATE TABLE ingestion.stage_execution",
                "CREATE TABLE ingestion.proposal (",
                "CREATE TABLE ingestion.proposal_review_decision",
                "CREATE TABLE ingestion.proposal_materialization",
                "UNIQUE(run_id, stage_code, stage_version, attempt_no)",
                "UNIQUE(proposal_id, target_kind)",
                "proposal_id uuid NOT NULL UNIQUE",
                "attempt_no <= max_attempts",
            ),
            label="orchestration migration",
        )
    )

    package_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    forbidden_fragments = (
        "from fastapi",
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
        "from google",
        "import tweepy",
        "import boto",
        "neo4j",
        "content_authoring",
    )
    leaked = [fragment for fragment in forbidden_fragments if fragment in package_source]
    if leaked:
        errors.append(
            "forbidden provider/HTTP/publication dependency leaked into orchestration: "
            + ", ".join(leaked)
        )

    if "publish(" in package_source or ".publish(" in package_source:
        errors.append("direct publication behavior leaked into orchestration package")

    expected_context_states = (
        'VERIFIED = "VERIFIED"',
        'CLAIMED = "CLAIMED"',
        'DISPUTED = "DISPUTED"',
        'UNKNOWN = "UNKNOWN"',
    )
    errors.extend(
        _require(
            context_models,
            expected_context_states,
            label="Context compatibility",
        )
    )
    if 'SUPPORTED = "SUPPORTED"' in context_models or 'FALSE = "FALSE"' in context_models:
        errors.append("canonical ClaimAssessment states leaked into Context presentation enum")

    if errors:
        print("Ingestion orchestration contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Ingestion orchestration contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

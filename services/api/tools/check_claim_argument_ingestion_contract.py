from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "claim-argument-ingestion.v1.yaml"
ADR = REPO_ROOT / "docs" / "adr" / "0027-first-class-claim-argument-normalized-ingestion.md"
MODELS = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "knowledge" / "models.py"
PORTS = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "knowledge" / "ports.py"
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260729_0015_claim_argument_knowledge.py"
)
CONTEXT_MODELS = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "context" / "models.py"
)


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [f"{label} missing: {fragment}" for fragment in fragments if fragment not in content]


def main() -> int:
    errors: list[str] = []
    for path in (CONTRACT, ADR, MODELS, PORTS, MIGRATION, CONTEXT_MODELS):
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = CONTRACT.read_text(encoding="utf-8")
    models = MODELS.read_text(encoding="utf-8")
    ports = PORTS.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    context_models = CONTEXT_MODELS.read_text(encoding="utf-8")

    errors.extend(
        _require(
            contract,
            (
                "claim_is_not_claimant: true",
                "claim_evaluation_is_versioned: true",
                "provider_specific_logic_ends_at_adapter: true",
                "existing_context_claim_status_contract_unchanged: true",
                "canonical_store: POSTGRESQL",
                "graph_database_required: false",
                "autonomous_case_publication_forbidden: true",
            ),
            label="architecture contract",
        )
    )
    errors.extend(
        _require(
            models,
            (
                "class Claim:",
                "class ClaimAssessment:",
                "class ClaimAssertion:",
                "class EvidenceLink:",
                "class ClaimRelation:",
                "class Argument:",
                "class ArgumentRelation:",
                "class SourceArtifact:",
                "class NormalizedArtifact:",
            ),
            label="knowledge domain",
        )
    )
    errors.extend(
        _require(
            ports,
            (
                "class SourceAdapter(Protocol):",
                "class KnowledgeRepository(Protocol):",
            ),
            label="ports",
        )
    )
    errors.extend(
        _require(
            migration,
            (
                "CREATE SCHEMA IF NOT EXISTS knowledge",
                "CREATE TABLE knowledge.source_artifact",
                "CREATE TABLE knowledge.normalized_artifact",
                "CREATE TABLE knowledge.claim (",
                "CREATE TABLE knowledge.claim_assessment",
                "CREATE TABLE knowledge.claim_assertion",
                "CREATE TABLE knowledge.evidence_link",
                "CREATE TABLE knowledge.claim_relation",
                "CREATE TABLE knowledge.argument (",
                "CREATE TABLE knowledge.argument_relation",
                "num_nonnulls(source_artifact_id, normalized_artifact_id) = 1",
                "num_nonnulls(claim_target_id, question_target_id, argument_target_id) = 1",
            ),
            label="knowledge migration",
        )
    )

    forbidden_provider_fragments = (
        "import requests",
        "import httpx",
        "import tweepy",
        "import boto",
        "from openai",
        "from google",
        "from meta",
    )
    knowledge_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in MODELS.parent.glob("*.py")
    )
    leaked = [
        fragment
        for fragment in forbidden_provider_fragments
        if fragment in knowledge_source
    ]
    if leaked:
        errors.append("provider-specific dependency leaked into knowledge domain: " + ", ".join(leaked))
    if "from fastapi" in knowledge_source:
        errors.append("HTTP framework leaked into knowledge domain")

    expected_context_states = (
        'VERIFIED = "VERIFIED"',
        'CLAIMED = "CLAIMED"',
        'DISPUTED = "DISPUTED"',
        'UNKNOWN = "UNKNOWN"',
    )
    errors.extend(_require(context_models, expected_context_states, label="Context compatibility"))
    if 'SUPPORTED = "SUPPORTED"' in context_models or 'FALSE = "FALSE"' in context_models:
        errors.append("canonical ClaimAssessment states leaked into Context presentation enum")

    if errors:
        print("Claim/Argument ingestion contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Claim/Argument ingestion contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

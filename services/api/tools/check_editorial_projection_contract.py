from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "editorial-projection.v1.yaml"
ADR = REPO_ROOT / "docs" / "adr" / "0029-reviewed-candidate-editorial-projection.md"
MODULE = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "editorial_projection"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_editorial_projection.py"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0019_editorial_projection.py"
)


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [f"{label} missing: {item}" for item in fragments if item not in content]


def main() -> int:
    errors = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in (CONTRACT, ADR, POSTGRES, MIGRATION)
        if not path.exists()
    ]
    if not MODULE.exists():
        errors.append(f"missing required module: {MODULE.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = CONTRACT.read_text(encoding="utf-8")
    service = (MODULE / "service.py").read_text(encoding="utf-8")
    models = (MODULE / "models.py").read_text(encoding="utf-8")
    ports = (MODULE / "ports.py").read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")

    errors.extend(
        _require(
            contract,
            (
                "candidate_case_is_not_case: true",
                "projection_is_explicit_editorial_action: true",
                "projection_is_atomic: true",
                "projection_is_idempotent: true",
                "projection_creates_draft_only: true",
                "automatic_review_approval_publication_forbidden: true",
                "provider_or_ai_dependency_in_projection_forbidden: true",
            ),
            label="architecture contract",
        )
    )
    errors.extend(
        _require(
            models,
            (
                "class ReviewedProposal:",
                "class EditorialProjectionProfile:",
                "class EditorialProjectionCommand:",
                "class EditorialProjectionRecord:",
            ),
            label="projection domain",
        )
    )
    errors.extend(
        _require(
            ports,
            (
                "class ReviewedProposalSource(Protocol):",
                "class EditorialProjectionRepository(Protocol):",
                "def create_atomically(",
            ),
            label="projection ports",
        )
    )
    errors.extend(
        _require(
            service,
            (
                'candidate.proposal_kind != "CANDIDATE_CASE"',
                'candidate.review_decision != "ACCEPTED"',
                'command="project_candidate_case"',
                "state=ContentLifecycle.DRAFT",
                "EDITORIAL_PROJECTION_FLOW_REFERENCE_INVALID",
                "get_by_idempotency(",
                "get_by_candidate(",
                "create_atomically(",
            ),
            label="projection service",
        )
    )
    errors.extend(
        _require(
            migration,
            (
                'revision = "20260802_0019"',
                'down_revision = "20260730_0018"',
                "CREATE TABLE editorial.projection_record",
                "candidate_proposal_id uuid NOT NULL UNIQUE",
                "authoring_case_id uuid NOT NULL UNIQUE",
                "authoring_case_version_id uuid NOT NULL UNIQUE",
                "UNIQUE(candidate_proposal_id, idempotency_key)",
            ),
            label="projection migration",
        )
    )
    errors.extend(
        _require(
            postgres,
            (
                "with self._engine.begin() as connection:",
                "INSERT INTO editorial.case_item",
                "INSERT INTO editorial.case_version",
                "INSERT INTO editorial.lifecycle_audit",
                "INSERT INTO editorial.projection_record",
            ),
            label="PostgreSQL atomic boundary",
        )
    )

    required_files = (CONTRACT, ADR, POSTGRES, MIGRATION, *MODULE.glob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in required_files if path.exists())
    forbidden = (
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "from fastapi",
        ".submit_for_review(",
        ".approve(",
        ".publish(",
    )
    leaked = [fragment for fragment in forbidden if fragment in source]
    if leaked:
        errors.append("forbidden dependency or lifecycle shortcut: " + ", ".join(leaked))

    if errors:
        print("Editorial Projection contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Editorial Projection contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "case-version-flow-pinning.v1.yaml"
SERVICE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "content_authoring"
    / "service.py"
)
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_flow_pinned_content_authoring.py"
)
CONSUMER = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_explore_decision.py"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260728_0012_case_flow_pinning.py"
)


def main() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    consumer = CONSUMER.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")

    problems: list[str] = []
    for fragment in {
        "runtime_uses_live_configuration: false",
        "immutable_after_publication: true",
        "re_resolve_on_publish: true",
        "content_configuration_id",
        "content_configuration_version_no",
        "resolved_flow",
    }:
        if fragment not in contract:
            problems.append(f"Flow pinning contract missing: {fragment}")

    for fragment in {
        "self._publication_configuration_resolver.resolve(version)",
        "content_configuration_id=resolution.content_configuration_id",
        "resolved_flow=resolution.resolved_flow",
        "content_configuration_id=None",
        "resolved_flow=None",
    }:
        if fragment not in service:
            problems.append(f"Authoring publication pinning missing: {fragment}")

    for fragment in {
        "class PostgresFlowPinnedContentAuthoringRepository",
        '"resolved_flow": cls._resolved_flow_document(version.resolved_flow)',
        "UPDATE content.case_version",
        "content_configuration_version_no = :content_configuration_version_no",
    }:
        if fragment not in postgres:
            problems.append(f"PostgreSQL Flow provenance adapter missing: {fragment}")

    for fragment in {
        "cv.content_configuration_id",
        "cv.content_configuration_version_no",
        "cv.resolved_flow",
        "resolved_flow=resolved_flow",
    }:
        if fragment not in consumer:
            problems.append(f"Consumer Flow provenance read missing: {fragment}")

    for fragment in {
        "ADD COLUMN content_configuration_id uuid",
        "ADD COLUMN content_configuration_version_no integer",
        "ADD COLUMN flow_template_code text",
        "ADD COLUMN flow_template_version_no integer",
        "ADD COLUMN resolved_flow jsonb",
    }:
        if fragment not in migration:
            problems.append(f"Flow pinning migration missing: {fragment}")

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Case Flow pinning contract OK: publication resolves current configuration, "
        "pins immutable Flow/config provenance and consumer reads the stored snapshot."
    )


if __name__ == "__main__":
    main()

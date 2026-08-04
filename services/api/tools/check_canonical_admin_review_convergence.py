from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
CONTRACT = ROOT / "docs/contracts/canonical-admin-feed-source-brief-review.v1.json"

REQUIRED_FILES = (
    API / "src/kefe_api/modules/admin_security/feed_item_review.py",
    API / "src/kefe_api/modules/admin_security/feed_item_review_router.py",
    API / "src/kefe_api/modules/admin_security/source_brief_ingestion.py",
    API / "src/kefe_api/modules/admin_security/source_brief_ingestion_router.py",
    API / "src/kefe_api/modules/admin_security/source_brief_review.py",
    API / "src/kefe_api/modules/admin_security/source_brief_review_router.py",
    API / "src/kefe_api/modules/ingestion_orchestration/source_brief_ingestion.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"canonical Admin review convergence failed: {message}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["source_issue"] == 289, "contract must reference Issue #289")
    require(contract["no_schema_migration"] is True, "slice must remain migration-free")
    require(
        contract["excluded_conflict_groups"] == ["PUBLIC_FEED_MODEL"],
        "public-feed alternatives must remain excluded",
    )
    for path in REQUIRED_FILES:
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    main_source = (API / "src/kefe_api/main.py").read_text(encoding="utf-8")
    markers = (
        "_api_at_least(settings.api_version, 0, 21)",
        "admin_feed_item_review_router",
        "_api_at_least(settings.api_version, 0, 22)",
        "admin_source_brief_ingestion_router",
        "_api_at_least(settings.api_version, 0, 23)",
        "admin_source_brief_review_router",
    )
    for marker in markers:
        require(marker in main_source, f"main.py missing {marker}")

    joined = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED_FILES)
    for forbidden in (
        "raw_body=",
        "backend_object_key",
        "automatic_review",
        "publish_case(",
        "approve_case(",
    ):
        require(forbidden not in joined, f"forbidden boundary found: {forbidden}")

    require("ProposalReviewDecisionKind.ACCEPTED" in joined, "accepted review precondition missing")
    require("complete_successful_stage" in joined, "atomic stage completion missing")
    require("require_source_brief_normalized_artifact" in joined, "lineage revalidation missing")
    print("canonical Admin review convergence architecture PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/canonical-candidate-bundle-projection.v1.json"
ADR = ROOT / "docs/adr/0099-canonical-source-brief-candidate-bundle-and-explicit-projection.md"
DOMAIN = ROOT / "services/api/src/kefe_api/modules/ingestion_orchestration/candidate_case_bundle.py"
SERVICE = ROOT / "services/api/src/kefe_api/modules/admin_security/candidate_bundle.py"
ROUTER = ROOT / "services/api/src/kefe_api/modules/admin_security/candidate_bundle_router.py"
PROJECTION_ROUTER = (
    ROOT / "services/api/src/kefe_api/modules/admin_security/editorial_projection_router.py"
)
POLICY = ROOT / "services/api/src/kefe_api/modules/admin_security/policy.py"
MAIN = ROOT / "services/api/src/kefe_api/main.py"
ERRORS = ROOT / "docs/contracts/error-codes.canonical-candidate-bundle.v1.yaml"
MEMORY_TEST = ROOT / "services/api/tests/test_canonical_candidate_bundle_projection_http.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"canonical candidate bundle architecture failed: {message}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["source_issue"] == 294, "contract must reference Issue #294")
    require(
        contract["parent_sha"] == "f6076229db05a27367726f4c48e5fc8212f7e96e",
        "parent exact SHA drifted",
    )
    require(
        contract["historical_source"]["wholesale_merge_forbidden"] is True,
        "historical candidate branch must not be merged wholesale",
    )
    require(
        contract["api"]["minimum_version"] == "0.25.0",
        "candidate bundle API version drifted",
    )
    require(contract["proposals"]["exact_count"] == 3, "bundle must emit 3 proposals")
    require(
        contract["projection"]["output_lifecycle"] == "DRAFT",
        "projection output must remain DRAFT",
    )
    for path, label in (
        (ADR, "ADR-0099"),
        (DOMAIN, "candidate bundle domain"),
        (SERVICE, "secured candidate bundle service"),
        (ROUTER, "candidate bundle router"),
        (PROJECTION_ROUTER, "editorial projection router"),
        (POLICY, "Admin policy"),
        (MAIN, "application composition"),
        (ERRORS, "candidate bundle error registry"),
        (MEMORY_TEST, "candidate bundle memory test"),
    ):
        require(path.is_file(), f"{label} is missing")

    domain = DOMAIN.read_text(encoding="utf-8")
    for marker in (
        'PIPELINE_CODE = "SOURCE_BRIEF_CANDIDATE_BUNDLE"',
        'STAGE_CODE = "BUILD_CANDIDATE_BUNDLE"',
        'DECISION_PROBLEM_KIND = "DECISION_PROBLEM"',
        'QUESTION_DRAFT_KIND = "QUESTION_DRAFT"',
        'CANDIDATE_CASE_KIND = "CANDIDATE_CASE"',
        'BUNDLE_RISK_CODE = "UNREVIEWED_CANDIDATE_BUNDLE"',
        "CandidateCaseEditorialConfiguration",
        "AcceptedSourceBriefCandidateSeed",
        "CandidateCaseBundleStageProcessor",
        "dependency_ids",
    ):
        require(marker in domain, f"candidate bundle domain missing {marker}")
    for forbidden in (
        "import requests",
        "import httpx",
        "AIExecution",
        "publish(",
        "approve(",
    ):
        require(forbidden not in domain, f"forbidden domain behavior leaked: {forbidden}")

    service = SERVICE.read_text(encoding="utf-8")
    for marker in (
        "AdminCapability.SOURCE_VERIFY",
        "self._source_briefs.detail(",
        "source_brief_review_decision_id",
        "ProposalReviewDecisionKind.ACCEPTED",
        "AcceptedSourceBriefCandidateSeed(",
        "self._knowledge.add_normalized_artifact(",
        "self._ingestion.start_run(",
        "self._repository.complete_successful_stage(",
        "CandidateBundleResult",
    ):
        require(marker in service, f"secured service missing {marker}")
    for forbidden in (
        ".review(",
        "add_review_decision(",
        "add_materialization(",
        ".project(",
        "publish(",
    ):
        require(forbidden not in service, f"service performs forbidden action: {forbidden}")

    router = ROUTER.read_text(encoding="utf-8")
    for marker in (
        "WritePrincipalDep",
        '"/source-briefs/{proposal_id}/candidate-bundle"',
        "CandidateCaseEditorialConfiguration(",
        'proposal_review_state="PENDING"',
    ):
        require(marker in router, f"candidate bundle router missing {marker}")
    for forbidden in (
        "raw_body",
        "backend_object_key",
        "secret_ref",
        '"payload"',
    ):
        require(forbidden not in router, f"router exposes forbidden field {forbidden}")

    main = MAIN.read_text(encoding="utf-8")
    for marker in (
        "admin_candidate_bundle_router",
        "_api_at_least(settings.api_version, 0, 25)",
        "app.include_router(admin_candidate_bundle_router)",
    ):
        require(marker in main, f"application composition missing {marker}")

    projection_router = PROJECTION_ROUTER.read_text(encoding="utf-8")
    require(
        '"/candidate-proposals/{candidate_proposal_id}/projection"' in projection_router,
        "existing explicit projection route is missing",
    )
    require(
        "projection.project(" in projection_router,
        "projection route must remain an explicit command",
    )
    policy = POLICY.read_text(encoding="utf-8")
    require("AdminCapability.CONTENT_PROJECT" in policy, "CONTENT_PROJECT policy is missing")

    error_source = ERRORS.read_text(encoding="utf-8")
    for code in (
        "ADMIN_CANDIDATE_BUNDLE_CONFIGURATION_INVALID",
        "ADMIN_CANDIDATE_BUNDLE_SOURCE_BRIEF_REVIEW_REQUIRED",
        "ADMIN_CANDIDATE_BUNDLE_SEED_CONFLICT",
        "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
        "ADMIN_CANDIDATE_BUNDLE_BUILD_INVALID",
    ):
        require(code in error_source, f"candidate bundle error registry missing {code}")

    test_source = MEMORY_TEST.read_text(encoding="utf-8")
    for marker in (
        "test_candidate_bundle_is_025_only_secured_explicit_and_idempotent",
        "test_candidate_bundle_projection_requires_separate_reviews_and_creates_one_draft",
        "assert blocked.status_code == 422",
        "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY",
        'assert first.json()["lifecycle_state"] == "DRAFT"',
        'assert replay.json()["replayed"] is True',
    ):
        require(marker in test_source, f"memory evidence missing {marker}")

    print("canonical candidate bundle architecture PASS")


if __name__ == "__main__":
    main()

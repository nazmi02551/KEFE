from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/contracts/public-case-version-history.v1.json"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(source: str, needle: str, *, where: str) -> None:
    assert needle in source, f"{where}: missing {needle!r}"


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["contract_id"] == "KEFE-PUBLIC-CASE-VERSION-HISTORY-001"
    assert contract["version"] == "1.0.0"
    assert contract["capabilities"] == ["CAP-072", "CAP-026", "CAP-095"]
    assert contract["public_api"] == {
        "method": "GET",
        "path": "/v1/cases/{case_id}/history",
        "authentication_required": False,
        "maximum_items": 20,
        "ordering": ["version_no DESC"],
        "allowed_source_statuses": ["PUBLISHED", "SUPERSEDED"],
        "public_classifications": ["CURRENT", "PREVIOUS"],
        "active_published_current_required": True,
        "empty_or_withdrawn_error": "CASE_NOT_FOUND",
    }

    models = read("services/api/src/kefe_api/modules/decision/models.py")
    for token in (
        "class PublicCaseVersionClassification(StrEnum):",
        'CURRENT = "CURRENT"',
        'PREVIOUS = "PREVIOUS"',
        "class PublicCaseVersion:",
    ):
        require(models, token, where="Decision history model")

    service = read("services/api/src/kefe_api/modules/decision/service.py")
    require(service, "bounded_limit = min(max(limit, 1), 20)", where="Decision service")
    require(service, 'DomainError("CASE_NOT_FOUND"', where="Decision service")

    router = read("services/api/src/kefe_api/modules/decision/router.py")
    require(router, '"/cases/{case_id}/history"', where="Decision API")
    require(router, "Query(ge=1, le=20)", where="Decision API")
    require(
        router,
        "classification: PublicCaseVersionClassification",
        where="Decision API classification",
    )
    for field in contract["item_fields"]:
        require(router, field, where="Decision API response")

    postgres = read(
        "services/api/src/kefe_api/infrastructure/postgres_explore_decision.py"
    )
    for token in (
        "ci.lifecycle_state = 'PUBLISHED'",
        "cv.status IN ('PUBLISHED', 'SUPERSEDED')",
        "current_version.status = 'PUBLISHED'",
        "ORDER BY cv.version_no DESC",
        "LIMIT :limit",
    ):
        require(postgres, token, where="PostgreSQL public history")
    for forbidden in (
        "editorial.case_version",
        "editorial.lifecycle_audit",
        "actor_ref",
        "rationale",
    ):
        assert forbidden not in postgres, (
            f"PostgreSQL public history must not expose editorial data: {forbidden}"
        )

    mobile_repository = read(
        "apps/mobile/lib/features/decision/data/http_decision_repository.dart"
    )
    for token in (
        "fetchPublicCaseHistory(String caseId)",
        "PublicCaseVersionClassification.current",
        "PublicCaseVersionClassification.previous",
        "PUBLIC_CASE_HISTORY_RESPONSE_INVALID",
        "!versionNumbers.add(versionNo)",
        "versionNo >= previousVersionNo",
        "currentCount != 1",
    ):
        require(mobile_repository, token, where="mobile public history parser")

    preview = read(
        "apps/mobile/lib/features/decision/data/preview_decision_repository.dart"
    )
    require(
        preview,
        "PublicCaseVersionClassification.current",
        where="Product Preview public history",
    )
    assert "PublicCaseVersionClassification.previous" not in preview, (
        "Product Preview must not invent a previous published version"
    )

    surface = read(
        "apps/mobile/lib/features/decision/presentation/case_version_history_section.dart"
    )
    for token in (
        "case-history-section",
        "case-history-unavailable",
        "case-history-retry",
        "case-history-expand",
    ):
        require(surface, token, where="mobile history surface")

    strings = read(
        "apps/mobile/lib/features/decision/presentation/case_version_history_strings.dart"
    )
    for token in (
        "'title'",
        "'helper'",
        "'unavailable'",
        "'current'",
        "'previous'",
        "'single'",
    ):
        assert strings.count(f"{token}:") == 2, (
            f"EN/TR localization missing for {token}"
        )
    require(
        strings,
        "does not by itself mean a correction",
        where="English non-inference copy",
    )
    require(
        strings,
        "tek başına düzeltme yapıldığı anlamına gelmez",
        where="Turkish non-inference copy",
    )

    legacy = read(
        "apps/mobile/lib/features/decision/presentation/decision_flow_screen.dart"
    )
    progressive = read(
        "apps/mobile/lib/features/decision/presentation/decision_experience_active_step.dart"
    )
    require(legacy, "CaseVersionHistorySection(caseId:", where="legacy Case journey")
    require(
        progressive,
        "CaseVersionHistorySection(caseId:",
        where="progressive Case journey",
    )

    openapi = json.loads(read("docs/contracts/openapi.v1.json"))
    path = openapi["paths"]["/v1/cases/{case_id}/history"]["get"]
    assert path.get("security", []) == []
    schemas = openapi["components"]["schemas"]
    assert schemas["PublicCaseVersionClassification"]["enum"] == [
        "CURRENT",
        "PREVIOUS",
    ]
    assert set(schemas["PublicCaseVersionResponse"]["required"]) == {
        "case_version_id",
        "version_no",
        "title",
        "summary",
        "published_at",
        "classification",
    }

    print("Bounded public CaseVersion history contract: PASS")


if __name__ == "__main__":
    main()

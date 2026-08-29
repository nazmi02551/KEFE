from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/contracts/kefe-today-real-event-projection.v1.json"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(source: str, needle: str, *, where: str) -> None:
    assert needle in source, f"{where}: missing {needle!r}"


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["contract_id"] == "KEFE-TODAY-REAL-EVENT-PROJECTION-001"
    assert contract["version"] == "1.0.0"
    assert contract["capabilities"] == ["CAP-026", "CAP-095"]
    assert contract["authority"] == {
        "source_model": "AuthoringCaseVersion.is_real_event",
        "review_mode_for_real_event": "SOURCE_VERIFICATION",
        "consumer_column": "content.case_version.is_real_event",
        "consumer_api_path": "/v1/cases",
        "consumer_api_field": "is_real_event",
    }
    assert contract["projection"]["legacy_default"] is False
    assert contract["projection"]["copy_exact_value"] is True
    assert all(
        contract["selection"][key] is False
        for key in (
            "client_reordering_allowed",
            "client_freshness_threshold_allowed",
            "format_inference_allowed",
            "domain_inference_allowed",
            "title_or_summary_inference_allowed",
            "risk_inference_allowed",
            "list_position_inference_allowed",
        )
    )

    migration = read(
        "services/api/migrations/versions/20260827_0037_case_version_real_event.py"
    )
    for token in (
        'revision = "20260827_0037"',
        'down_revision = "20260812_0036"',
        "ALTER TABLE content.case_version",
        "ADD COLUMN is_real_event boolean NOT NULL DEFAULT false",
    ):
        require(migration, token, where="migration")

    authoring_models = read(
        "services/api/src/kefe_api/modules/content_authoring/models.py"
    )
    require(
        authoring_models,
        "is_real_event: bool = False",
        where="authoring source model",
    )
    policy = read("services/api/src/kefe_api/modules/content_configuration/policy.py")
    require(
        policy,
        "if version.is_fact_bearing or version.is_real_event:",
        where="content review policy",
    )
    require(policy, 'required.add("SOURCE_VERIFICATION")', where="content review policy")

    materialization = read(
        "services/api/src/kefe_api/infrastructure/postgres_content_authoring.py"
    )
    require(materialization, ":is_real_event", where="consumer materialization")
    require(
        materialization,
        '"is_real_event": version.is_real_event',
        where="consumer materialization",
    )

    decision_models = read("services/api/src/kefe_api/modules/decision/models.py")
    require(decision_models, "is_real_event: bool = False", where="Decision CaseVersion")
    for adapter_path in (
        "services/api/src/kefe_api/infrastructure/postgres_decision.py",
        "services/api/src/kefe_api/infrastructure/postgres_explore_decision.py",
    ):
        adapter = read(adapter_path)
        require(adapter, "cv.is_real_event", where=adapter_path)
        require(adapter, 'is_real_event=row["is_real_event"]', where=adapter_path)

    router = read("services/api/src/kefe_api/modules/decision/router.py")
    require(router, "class CaseSummaryResponse(BaseModel):", where="Decision API")
    require(router, "is_real_event: bool", where="Decision API")
    require(router, "is_real_event=case.is_real_event", where="Decision API")

    mobile_models = read(
        "apps/mobile/lib/features/decision/domain/decision_models.dart"
    )
    require(mobile_models, "this.isRealEvent = false", where="mobile summary")
    http_repository = read(
        "apps/mobile/lib/features/decision/data/http_decision_repository.dart"
    )
    require(
        http_repository,
        "isRealEvent: item['is_real_event'] == true",
        where="mobile API parser",
    )

    hub = read(
        "apps/mobile/lib/features/explore/presentation/experience_hub_screen.dart"
    )
    require(hub, "if (today == null && item.isRealEvent)", where="Experience Hub")
    assert hub.count("today = item;") == 1, "Today selection must have one assignment"
    require(hub, "experience-today-empty", where="Experience Hub")
    require(hub, "context.push('/case/${_todayCase!.id}')", where="Experience Hub")
    assert "DateTime" not in hub, "Experience Hub must not infer Today freshness"

    preview = read(
        "apps/mobile/lib/features/decision/data/preview_decision_repository.dart"
    )
    assert "isRealEvent: true" not in preview, (
        "Product Preview must not invent a governed real-event fixture"
    )

    catalog = read(
        "apps/mobile/lib/core/localization/experience_hub_string_catalog.dart"
    )
    for token in ("'today_title'", "'today_body'", "'today_action'", "'today_empty'"):
        assert catalog.count(token) == 2, f"EN/TR localization missing for {token}"

    mobile_tests = read("apps/mobile/test/experience_hub_test.dart")
    require(mobile_tests, "experience-today-empty", where="mobile regression")
    require(mobile_tests, "experience-today", where="mobile regression")
    require(mobile_tests, "post-commit-journey", where="mobile regression")
    parser_tests = read("apps/mobile/test/kefe_today_projection_test.dart")
    require(parser_tests, "repositoryFor('true')", where="mobile parser regression")
    require(parser_tests, "repositoryFor(null)", where="mobile parser regression")

    schema_contract = json.loads(
        read("docs/contracts/connected-alpha-schema-snapshot.v1.json")
    )
    assert schema_contract["canonical_chain"]["expected_head"] == "20260829_0040"
    assert schema_contract["canonical_chain"]["expected_migration_file_count"] == 40

    print("KEFE Today governed real-event projection contract: PASS")


if __name__ == "__main__":
    main()

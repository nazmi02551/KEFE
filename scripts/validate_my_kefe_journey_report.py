from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/my-kefe-journey-report.v1.json"
ADR = ROOT / "docs/adr/0138-actor-scoped-my-kefe-journey-report.md"
MODELS = ROOT / "services/api/src/kefe_api/modules/progress/models.py"
PORTS = ROOT / "services/api/src/kefe_api/modules/progress/ports.py"
SERVICE = ROOT / "services/api/src/kefe_api/modules/progress/service.py"
ROUTER = ROOT / "services/api/src/kefe_api/modules/progress/router.py"
MEMORY = ROOT / "services/api/src/kefe_api/modules/progress/in_memory.py"
POSTGRES = ROOT / "services/api/src/kefe_api/infrastructure/postgres_progress.py"
OPENAPI = ROOT / "docs/contracts/openapi.v1.json"
MOBILE_MODELS = ROOT / "apps/mobile/lib/features/progress/domain/progress_models.dart"
MOBILE_HTTP = ROOT / "apps/mobile/lib/features/progress/data/http_progress_repository.dart"
MOBILE_PREVIEW = ROOT / "apps/mobile/lib/features/progress/data/preview_progress_repository.dart"
MOBILE_SCREEN = (
    ROOT
    / "apps/mobile/lib/features/progress/presentation/my_kefe_personal_report_screen.dart"
)
MOBILE_ENTRY = (
    ROOT / "apps/mobile/lib/features/progress/presentation/my_kefe_journey_summary.dart"
)
MOBILE_APP = ROOT / "apps/mobile/lib/app/kefe_app.dart"
MOBILE_PREVIEW_APP = ROOT / "apps/mobile/lib/app/product_preview_app.dart"
MOBILE_STRINGS = (
    ROOT / "apps/mobile/lib/features/progress/localization/progress_string_catalog.dart"
)
MOBILE_TEST = ROOT / "apps/mobile/test/my_kefe_personal_report_test.dart"
MOBILE_PARITY_TEST = ROOT / "apps/mobile/test/phone_surface_parity_test.dart"


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [f"{label} missing: {fragment}" for fragment in fragments if fragment not in content]


def _class_fields(source: str, class_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
            }
    return set()


def main() -> int:
    errors: list[str] = []
    paths = (
        CONTRACT,
        ADR,
        MODELS,
        PORTS,
        SERVICE,
        ROUTER,
        MEMORY,
        POSTGRES,
        OPENAPI,
        MOBILE_MODELS,
        MOBILE_HTTP,
        MOBILE_PREVIEW,
        MOBILE_SCREEN,
        MOBILE_ENTRY,
        MOBILE_APP,
        MOBILE_PREVIEW_APP,
        MOBILE_STRINGS,
        MOBILE_TEST,
        MOBILE_PARITY_TEST,
    )
    for path in paths:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("issue") != 387:
        errors.append("personal report issue must remain #387")
    if contract.get("capabilities") != ["CAP-120"]:
        errors.append("personal report must remain scoped to CAP-120")

    surface = contract.get("surface", {})
    expected_surface = {
        "method": "GET",
        "path": "/v1/me/progress",
        "additive_member": "personal_report",
        "authentication": "ACTOR_BEARER",
        "actor_scoped": True,
        "missing_member_mobile_fallback": "EMPTY_REPORT",
    }
    if surface != expected_surface:
        errors.append("personal report HTTP surface changed")

    moments = contract.get("moments", {})
    if set(moments.get("allowed_types", [])) != {
        "INITIAL_COMMIT",
        "DECISION_UPDATE",
        "REFLECTION_COMPLETED",
    }:
        errors.append("personal report moment types changed")
    if moments.get("limit") != 24:
        errors.append("personal report limit must remain 24")
    if moments.get("ordering") != (
        "OCCURRED_AT_DESC_THEN_INTERNAL_SOURCE_ID_DESC"
    ):
        errors.append("personal report ordering must remain deterministic")

    persistence = contract.get("persistence", {})
    for key in (
        "reconstructed_on_read",
        "memory_postgres_parity_required",
        "account_continuity_preserved",
        "self_service_deletion_uses_canonical_record_deletion",
    ):
        if persistence.get(key) is not True:
            errors.append(f"personal report must require {key}")
    for key in ("new_table", "migration_required", "analytics_projection_dependency"):
        if persistence.get(key) is not False:
            errors.append(f"personal report must forbid {key}")

    model_fields = _class_fields(MODELS.read_text(encoding="utf-8"), "PersonalReportMoment")
    if model_fields != {
        "moment_type",
        "source_id",
        "case_id",
        "case_version_id",
        "title",
        "primary_domain",
        "occurred_at",
        "revision_no",
    }:
        errors.append(f"personal report domain fields changed: {sorted(model_fields)}")

    errors.extend(
        _require(
            PORTS.read_text(encoding="utf-8") + SERVICE.read_text(encoding="utf-8"),
            (
                "def get_personal_report(",
                "moment_limit=24",
            ),
            label="personal report port/service",
        )
    )
    errors.extend(
        _require(
            MEMORY.read_text(encoding="utf-8"),
            (
                "PersonalReportMomentType.INITIAL_COMMIT",
                "PersonalReportMomentType.DECISION_UPDATE",
                "PersonalReportMomentType.REFLECTION_COMPLETED",
                "item.occurred_at, item.source_id.hex",
                "moments[:moment_limit]",
            ),
            label="memory personal report",
        )
    )
    errors.extend(
        _require(
            POSTGRES.read_text(encoding="utf-8"),
            (
                "'INITIAL_COMMIT' AS moment_type",
                "'DECISION_UPDATE' AS moment_type",
                "'REFLECTION_COMPLETED' AS moment_type",
                "ws.actor_id = :actor_id",
                "dr.actor_id = :actor_id",
                "rc.actor_id = :actor_id",
                "ORDER BY occurred_at DESC, source_id DESC",
                "LIMIT :moment_limit",
            ),
            label="PostgreSQL personal report",
        )
    )

    router = ROUTER.read_text(encoding="utf-8")
    errors.extend(
        _require(
            router,
            (
                "class PersonalReportMomentResponse(BaseModel):",
                "class PersonalReportResponse(BaseModel):",
                "personal_report: PersonalReportResponse",
                '"personal_report_semantics": "OBSERVED_MOMENTS_ONLY"',
            ),
            label="personal report response",
        )
    )

    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    schemas = openapi.get("components", {}).get("schemas", {})
    moment_schema = schemas.get("PersonalReportMomentResponse", {})
    properties = set(moment_schema.get("properties", {}))
    expected_properties = set(moments.get("returned_fields", []))
    if properties != expected_properties:
        errors.append(f"personal report OpenAPI fields changed: {sorted(properties)}")
    envelope = schemas.get("ProgressEnvelopeResponse", {}).get("properties", {})
    if envelope.get("personal_report", {}).get("$ref") != (
        "#/components/schemas/PersonalReportResponse"
    ):
        errors.append("progress OpenAPI must expose PersonalReportResponse")
    forbidden = set(contract.get("forbidden_output", []))
    forbidden_openapi = {
        "ACTOR_ID": "actor_id",
        "SESSION_ID": "session_id",
        "REVISION_ID": "revision_id",
        "REFLECTION_COMPLETION_ID": "reflection_completion_id",
        "RAW_RESPONSE": "raw_response",
        "PRIVATE_REASON": "private_reason",
        "DECISION_DELTA": "decision_delta",
    }
    leaked = sorted(
        name
        for contract_name, name in forbidden_openapi.items()
        if contract_name in forbidden and name in properties
    )
    if leaked:
        errors.append(f"personal report OpenAPI leaks forbidden fields: {leaked}")

    mobile = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            MOBILE_MODELS,
            MOBILE_HTTP,
            MOBILE_PREVIEW,
            MOBILE_SCREEN,
            MOBILE_ENTRY,
            MOBILE_APP,
            MOBILE_PREVIEW_APP,
            MOBILE_PARITY_TEST,
        )
    )
    errors.extend(
        _require(
            mobile,
            (
                "enum MyKefeReportMomentType",
                "class MyKefePersonalReport",
                "body.containsKey('personal_report')",
                "Personal report exceeds its bounded limit",
                "MyKefePersonalReportScreen",
                "'/my-kefe/report'",
                "'/case/${moment.caseId}'",
                "my-kefe-report-no-inference",
                "DETERMINISTIC_PREVIEW",
            ),
            label="mobile personal report",
        )
    )
    strings = MOBILE_STRINGS.read_text(encoding="utf-8")
    for key in (
        "report.hero_title",
        "report.initial_commit",
        "report.decision_update",
        "report.reflection_completed",
        "report.non_inference",
    ):
        if strings.count(f"'{key}'") != 2:
            errors.append(f"personal report locale key must have TR/EN parity: {key}")

    if errors:
        print("My KEFE journey report contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("My KEFE journey report contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

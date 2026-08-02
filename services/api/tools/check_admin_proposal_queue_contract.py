from __future__ import annotations

import json
from pathlib import Path

from export_openapi import load_expected_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
CONTRACT = CONTRACTS / "admin-proposal-review-queue-slice36.v1.json"
POLICY = CONTRACTS / "admin-http-surface.v1.yaml"
OPENAPI = CONTRACTS / "openapi.v1.json"
ADMIN = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
)
ROUTER = ADMIN / "proposal_queue_router.py"
SERVICE = ADMIN / "proposal_queue.py"
MEMORY = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "ingestion_orchestration"
    / "in_memory.py"
)
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_proposal_review_queue.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
MEMORY_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_admin_proposal_queue_http.py"
)
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_admin_proposal_queue_http_postgres.py"
)
LIST_PATH = "/internal/admin/v1/proposals"
DETAIL_PATH = "/internal/admin/v1/proposals/{proposal_id}"


def _require(
    problems: list[str],
    label: str,
    content: str,
    fragments: tuple[str, ...],
) -> None:
    for fragment in fragments:
        if fragment not in content:
            problems.append(f"{label} missing: {fragment}")


def _response_schema_name(operation: dict, status: str) -> str:
    return (
        operation.get("responses", {})
        .get(status, {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
        .rsplit("/", 1)[-1]
    )


def main() -> int:
    required = (
        CONTRACT,
        POLICY,
        OPENAPI,
        ROUTER,
        SERVICE,
        MEMORY,
        POSTGRES,
        MAIN,
        MEMORY_TEST,
        POSTGRES_TEST,
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required file: {path.relative_to(REPO_ROOT)}")
        return 1

    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    policy = POLICY.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    openapi = load_expected_contract(OPENAPI)

    queue = contract.get("queue", {})
    if queue.get("pagination") != "OPAQUE_KEYSET_CURSOR":
        problems.append("queue pagination must be opaque keyset cursor")
    if queue.get("offset_supported") is not False:
        problems.append("offset pagination must be forbidden")
    if queue.get("maximum_limit") != 100:
        problems.append("queue maximum limit must remain 100")
    if queue.get("payload_in_list") is not False:
        problems.append("queue list must exclude arbitrary Proposal payload")
    if contract.get("detail", {}).get("immutable_payload_included") is not True:
        problems.append("Proposal detail must include immutable payload")

    _require(
        problems,
        "Admin HTTP policy",
        policy,
        (
            "proposal_queue_facade: SecuredProposalQueueService",
            "path: /proposals",
            "pagination: opaque_keyset_cursor",
            "offset_pagination: forbidden",
            "payload_in_list: false",
            "path: /proposals/{proposal_id}",
            "immutable_payload_included: true",
            "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID",
        ),
    )
    _require(
        problems,
        "Proposal queue router",
        router,
        (
            'prefix="/internal/admin/v1"',
            '@router.get("/proposals"',
            '@router.get("/proposals/{proposal_id}"',
            "principal: ReadPrincipalDep",
            "limit: Annotated[int, Query(ge=1, le=100)] = 50",
            "class ProposalQueueItemResponse(StrictModel):",
            "class ProposalDetailResponse(ProposalQueueItemResponse):",
        ),
    )
    if "payload:" in router.split("class ProposalQueueItemResponse", 1)[1].split(
        "class ProposalQueueResponse", 1
    )[0]:
        problems.append("Proposal queue list response contains payload")

    _require(
        problems,
        "Proposal queue service",
        service,
        (
            "AdminCapability.CONTENT_REVIEW",
            "limit=limit + 1",
            "rows[:limit]",
            "self._encode_cursor(items[-1])",
            "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID",
            "set(payload)",
            "created_at.tzinfo is None",
        ),
    )
    for forbidden in (
        ".review(",
        ".project(",
        ".publish(",
        "CONTENT_PROJECT",
        "CONTENT_PUBLISH",
    ):
        if forbidden in service:
            problems.append(f"Proposal queue service contains forbidden behavior: {forbidden}")

    _require(
        problems,
        "memory queue repository",
        memory,
        (
            "def list_proposal_queue(",
            "def get_proposal_queue_record(",
            "records.sort(",
            "item.proposal.created_at",
            "key <= cursor_key",
        ),
    )
    _require(
        problems,
        "PostgreSQL queue repository",
        postgres,
        (
            "LEFT JOIN ingestion.proposal_review_decision",
            "(p.created_at, p.id) > (:after_created_at, :after_proposal_id)",
            "ORDER BY p.created_at ASC, p.id ASC LIMIT :limit",
            "rd.id IS NULL",
            "def get_proposal_queue_record(",
        ),
    )
    if " OFFSET " in postgres.upper():
        problems.append("PostgreSQL Proposal queue may not use OFFSET pagination")
    if "app.include_router(admin_proposal_queue_router)" not in main_source:
        problems.append("application does not include Proposal queue router")

    _require(
        problems,
        "memory HTTP evidence",
        memory_test,
        (
            "test_queue_is_authorized_keyset_paginated_and_list_excludes_payload",
            "test_queue_filters_invalid_cursor_and_review_state_refresh",
            'assert all("payload" not in item',
        ),
    )
    _require(
        problems,
        "PostgreSQL HTTP evidence",
        postgres_test,
        (
            "test_postgres_admin_proposal_queue_paginates_filters_and_refreshes_review",
            'assert all("payload" not in item',
            "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID",
        ),
    )

    paths = openapi.get("paths", {})
    list_operation = paths.get(LIST_PATH, {}).get("get")
    detail_operation = paths.get(DETAIL_PATH, {}).get("get")
    if list_operation is None:
        problems.append(f"OpenAPI missing GET {LIST_PATH}")
    if detail_operation is None:
        problems.append(f"OpenAPI missing GET {DETAIL_PATH}")
    if list_operation is not None:
        names = {
            parameter.get("name")
            for parameter in list_operation.get("parameters", [])
        }
        if "offset" in names:
            problems.append("OpenAPI exposes forbidden offset parameter")
        for expected in (
            "limit",
            "cursor",
            "review_state",
            "proposal_kind",
            "risk_code",
            "run_id",
            "pipeline_code",
        ):
            if expected not in names:
                problems.append(f"OpenAPI list missing parameter: {expected}")
        limit_parameter = next(
            (
                parameter
                for parameter in list_operation.get("parameters", [])
                if parameter.get("name") == "limit"
            ),
            {},
        )
        if limit_parameter.get("schema", {}).get("maximum") != 100:
            problems.append("OpenAPI queue limit maximum is not 100")
        schema_name = _response_schema_name(list_operation, "200")
        item_ref = (
            openapi.get("components", {})
            .get("schemas", {})
            .get(schema_name, {})
            .get("properties", {})
            .get("items", {})
            .get("items", {})
            .get("$ref", "")
            .rsplit("/", 1)[-1]
        )
        item_properties = (
            openapi.get("components", {})
            .get("schemas", {})
            .get(item_ref, {})
            .get("properties", {})
        )
        if "payload" in item_properties:
            problems.append("OpenAPI Proposal queue item leaks payload")
    if detail_operation is not None:
        schema_name = _response_schema_name(detail_operation, "200")
        detail_properties = (
            openapi.get("components", {})
            .get("schemas", {})
            .get(schema_name, {})
            .get("properties", {})
        )
        if "payload" not in detail_properties:
            problems.append("OpenAPI Proposal detail omits immutable payload")

    if problems:
        print("Admin Proposal review queue contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Admin Proposal review queue contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

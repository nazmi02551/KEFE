from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path

from export_openapi import _merge_overlay, build_openapi

from kefe_api.core.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
BASE = CONTRACTS / "openapi.v1.json"
BEFORE_OPERATIONAL_REPORTS_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-mvp.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-case-builder.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-editorial-quality-review.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-flow-composer.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-publication-operations.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-community-reason-moderation.v0.19.overlay.json",
)
EXPECTED_PATHS = ("/internal/admin/v1/operational-reports/snapshot",)


def _load_before_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for overlay_path in BEFORE_OPERATIONAL_REPORTS_OVERLAYS:
        _merge_overlay(
            expected,
            json.loads(overlay_path.read_text(encoding="utf-8")),
            overlay_path.name,
        )
    return expected


def _build_runtime_openapi() -> dict[str, object]:
    previous = os.environ.get("KEFE_API_VERSION")
    os.environ["KEFE_API_VERSION"] = "0.19.0"
    get_settings.cache_clear()
    try:
        return build_openapi()
    finally:
        if previous is None:
            os.environ.pop("KEFE_API_VERSION", None)
        else:
            os.environ["KEFE_API_VERSION"] = previous
        get_settings.cache_clear()


def _collect_schema_refs(value: object, referenced: set[str]) -> None:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            referenced.add(ref.rsplit("/", 1)[-1])
        for item in value.values():
            _collect_schema_refs(item, referenced)
    elif isinstance(value, list):
        for item in value:
            _collect_schema_refs(item, referenced)


def build_overlay() -> dict[str, object]:
    before = _load_before_contract()
    generated = _build_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.19.0":
        raise SystemExit("Operational Reports overlay expects API version 0.19.0")

    before_paths = before.get("paths", {})
    generated_paths = generated.get("paths", {})
    before_schemas = before.get("components", {}).get("schemas", {})
    generated_schemas = generated.get("components", {}).get("schemas", {})
    if not isinstance(before_paths, dict) or not isinstance(generated_paths, dict):
        raise SystemExit("OpenAPI paths must be objects")
    if not isinstance(before_schemas, dict) or not isinstance(generated_schemas, dict):
        raise SystemExit("OpenAPI schemas must be objects")

    changed_paths = sorted(
        path
        for path in before_paths.keys() & generated_paths.keys()
        if before_paths[path] != generated_paths[path]
    )
    removed_paths = sorted(before_paths.keys() - generated_paths.keys())
    changed_schemas = sorted(
        name
        for name in before_schemas.keys() & generated_schemas.keys()
        if before_schemas[name] != generated_schemas[name]
    )
    removed_schemas = sorted(before_schemas.keys() - generated_schemas.keys())
    if changed_paths or removed_paths or changed_schemas or removed_schemas:
        raise SystemExit(
            "Operational Reports API must remain additive; "
            f"changed_paths={changed_paths}, removed_paths={removed_paths}, "
            f"changed_schemas={changed_schemas}, removed_schemas={removed_schemas}"
        )

    missing_paths = sorted(set(EXPECTED_PATHS) - set(generated_paths))
    already_present = sorted(set(EXPECTED_PATHS) & set(before_paths))
    if missing_paths or already_present:
        raise SystemExit(
            "Operational Reports overlay path boundary drifted; "
            f"missing={missing_paths}, already_present={already_present}"
        )

    referenced: set[str] = set()
    for path in EXPECTED_PATHS:
        _collect_schema_refs(generated_paths[path], referenced)

    processed: set[str] = set()
    while pending := sorted(referenced - processed):
        for name in pending:
            schema = generated_schemas.get(name)
            if schema is None:
                raise SystemExit(f"Operational Reports overlay references missing schema: {name}")
            processed.add(name)
            _collect_schema_refs(schema, referenced)

    new_schema_names = set(generated_schemas) - set(before_schemas)
    additive_schema_names = sorted(referenced & new_schema_names)
    return {
        "target_version": "0.19.0",
        "components": {
            "schemas": {name: generated_schemas[name] for name in additive_schema_names}
        },
        "paths": {path: generated_paths[path] for path in EXPECTED_PATHS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate additive Admin Operational Reports OpenAPI overlay"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    overlay = build_overlay()
    rendered = json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists():
            raise SystemExit("Checked-in Operational Reports overlay is missing")
        if json.loads(args.output.read_text(encoding="utf-8")) != overlay:
            raise SystemExit("Checked-in Operational Reports overlay is stale")
        print(f"Operational Reports OpenAPI overlay matches {args.output}")
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(f"Operational Reports OpenAPI overlay written to {args.output}")


if __name__ == "__main__":
    main()

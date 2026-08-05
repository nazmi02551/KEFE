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
BEFORE_PUBLICATION_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-mvp.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-case-builder.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-editorial-quality-review.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-flow-composer.v0.19.overlay.json",
)
EXPECTED_PATHS = [
    "/internal/admin/v1/publication-operations",
    "/internal/admin/v1/publication-operations/{version_id}",
    "/internal/admin/v1/publication-operations/{version_id}/decision",
    "/internal/admin/v1/publication-operations/{version_id}/preflight",
]


def _load_before_publication_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for path in BEFORE_PUBLICATION_OVERLAYS:
        _merge_overlay(expected, json.loads(path.read_text(encoding="utf-8")), path.name)
    return expected


def _build_publication_runtime_openapi() -> dict[str, object]:
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


def build_overlay() -> dict[str, object]:
    before = _load_before_publication_contract()
    generated = _build_publication_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.19.0":
        raise SystemExit("Publication Operations overlay expects API version 0.19.0")

    before_schemas = before.get("components", {}).get("schemas", {})
    generated_schemas = generated.get("components", {}).get("schemas", {})
    before_paths = before.get("paths", {})
    generated_paths = generated.get("paths", {})

    changed_schemas = sorted(
        name
        for name in before_schemas.keys() & generated_schemas.keys()
        if before_schemas[name] != generated_schemas[name]
    )
    removed_schemas = sorted(before_schemas.keys() - generated_schemas.keys())
    changed_paths = sorted(
        path
        for path in before_paths.keys() & generated_paths.keys()
        if before_paths[path] != generated_paths[path]
    )
    removed_paths = sorted(before_paths.keys() - generated_paths.keys())
    if changed_schemas or removed_schemas or changed_paths or removed_paths:
        raise SystemExit(
            "Publication Operations API must remain additive; "
            f"changed_schemas={changed_schemas}, removed_schemas={removed_schemas}, "
            f"changed_paths={changed_paths}, removed_paths={removed_paths}"
        )

    missing_paths = sorted(set(EXPECTED_PATHS) - set(generated_paths))
    already_present = sorted(set(EXPECTED_PATHS) & set(before_paths))
    if missing_paths or already_present:
        raise SystemExit(
            "Publication Operations overlay path boundary drifted; "
            f"missing={missing_paths}, already_present={already_present}"
        )
    new_path_names = sorted(EXPECTED_PATHS)

    referenced_schema_names: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                referenced_schema_names.add(ref.rsplit("/", 1)[-1])
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    for path in new_path_names:
        collect(generated_paths[path])

    processed: set[str] = set()
    while pending := sorted(referenced_schema_names - processed):
        for name in pending:
            schema = generated_schemas.get(name)
            if schema is None:
                raise SystemExit(
                    f"Publication Operations overlay references missing schema: {name}"
                )
            processed.add(name)
            collect(schema)

    new_schema_names = set(generated_schemas.keys()) - set(before_schemas.keys())
    additive_schema_names = sorted(referenced_schema_names & new_schema_names)
    return {
        "target_version": "0.19.0",
        "components": {
            "schemas": {name: generated_schemas[name] for name in additive_schema_names}
        },
        "paths": {path: generated_paths[path] for path in new_path_names},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate additive Admin Publication Operations OpenAPI overlay"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    overlay = build_overlay()
    rendered = json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists():
            raise SystemExit("Checked-in Publication Operations overlay is missing")
        checked = json.loads(args.output.read_text(encoding="utf-8"))
        if checked != overlay:
            raise SystemExit("Checked-in Publication Operations overlay is stale")
        print(f"Publication Operations OpenAPI overlay matches {args.output}")
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(f"Publication Operations OpenAPI overlay written to {args.output}")


if __name__ == "__main__":
    main()

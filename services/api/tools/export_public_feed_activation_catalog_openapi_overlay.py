from __future__ import annotations

import argparse
import json
import os
import re
from copy import deepcopy
from pathlib import Path

from export_openapi import _merge_overlay, build_openapi

from kefe_api.core.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
BASE = CONTRACTS / "openapi.v1.json"
BEFORE_CATALOG_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-mvp.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
)
CATALOG_PATHS = (
    "/internal/admin/v1/public-feed-activations",
    "/internal/admin/v1/public-feed-activations/{activation_code}",
)
_SCHEMA_REF = re.compile(r"^#/components/schemas/([^/]+)$")


def _load_before_catalog_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for path in BEFORE_CATALOG_OVERLAYS:
        _merge_overlay(expected, json.loads(path.read_text(encoding="utf-8")), path.name)
    return expected


def _build_catalog_runtime_openapi() -> dict[str, object]:
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


def _referenced_schema_names(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str):
            match = _SCHEMA_REF.fullmatch(reference)
            if match is not None:
                found.add(match.group(1))
        for child in value.values():
            found.update(_referenced_schema_names(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_referenced_schema_names(child))
    return found


def _catalog_schema_names(
    *,
    selected_paths: dict[str, object],
    generated_schemas: dict[str, object],
    before_schemas: dict[str, object],
) -> tuple[str, ...]:
    pending = list(_referenced_schema_names(selected_paths))
    selected: set[str] = set()
    while pending:
        name = pending.pop()
        if name in selected or name in before_schemas:
            continue
        schema = generated_schemas.get(name)
        if schema is None:
            raise SystemExit(f"Activation catalog schema reference is missing: {name}")
        selected.add(name)
        pending.extend(_referenced_schema_names(schema) - selected)
    return tuple(sorted(selected))


def build_overlay() -> dict[str, object]:
    before = _load_before_catalog_contract()
    generated = _build_catalog_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.19.0":
        raise SystemExit(
            "Activation catalog overlay generator expects runtime API version 0.19.0"
        )

    before_schemas = before.get("components", {}).get("schemas", {})
    generated_schemas = generated.get("components", {}).get("schemas", {})
    changed_schemas = sorted(
        name
        for name in before_schemas.keys() & generated_schemas.keys()
        if before_schemas[name] != generated_schemas[name]
    )
    removed_schemas = sorted(before_schemas.keys() - generated_schemas.keys())
    if changed_schemas or removed_schemas:
        raise SystemExit(
            "Activation catalog API must remain additive; "
            f"changed={changed_schemas}, removed={removed_schemas}"
        )

    before_paths = before.get("paths", {})
    generated_paths = generated.get("paths", {})
    changed_paths = sorted(
        path
        for path in before_paths.keys() & generated_paths.keys()
        if before_paths[path] != generated_paths[path]
    )
    removed_paths = sorted(before_paths.keys() - generated_paths.keys())
    if changed_paths or removed_paths:
        raise SystemExit(
            "Activation catalog API must remain additive; "
            f"changed={changed_paths}, removed={removed_paths}"
        )

    selected_paths: dict[str, object] = {}
    for path in CATALOG_PATHS:
        if path in before_paths:
            raise SystemExit(f"Activation catalog path already exists before overlay: {path}")
        try:
            selected_paths[path] = generated_paths[path]
        except KeyError as exc:
            raise SystemExit(f"Activation catalog path is missing: {path}") from exc
    schema_names = _catalog_schema_names(
        selected_paths=selected_paths,
        generated_schemas=generated_schemas,
        before_schemas=before_schemas,
    )
    return {
        "target_version": "0.19.0",
        "components": {
            "schemas": {name: generated_schemas[name] for name in schema_names}
        },
        "paths": selected_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate additive public feed activation catalog OpenAPI overlay"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    overlay = build_overlay()
    rendered = json.dumps(
        overlay,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.check:
        if not args.output.exists():
            raise SystemExit("Checked-in activation catalog OpenAPI overlay is missing")
        try:
            checked = json.loads(args.output.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(
                "Checked-in activation catalog OpenAPI overlay is invalid JSON"
            ) from exc
        if checked != overlay:
            raise SystemExit("Checked-in activation catalog OpenAPI overlay is stale")
        print(f"Activation catalog OpenAPI overlay matches {args.output}")
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(f"Activation catalog OpenAPI overlay written to {args.output}")


if __name__ == "__main__":
    main()

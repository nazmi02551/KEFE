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
PRE_GLOBAL_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-mvp.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-feed-item-materialization.v0.19.overlay.json",
)


def _load_pre_global_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for path in PRE_GLOBAL_OVERLAYS:
        _merge_overlay(expected, json.loads(path.read_text(encoding="utf-8")), path.name)
    return expected


def _build_global_runtime_openapi() -> dict[str, object]:
    previous = os.environ.get("KEFE_API_VERSION")
    os.environ["KEFE_API_VERSION"] = "0.20.0"
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
    before = _load_pre_global_contract()
    generated = _build_global_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.20.0":
        raise SystemExit("Global OpenAPI overlay generator expects runtime API version 0.20.0")

    before_schemas = before.get("components", {}).get("schemas", {})
    generated_schemas = generated.get("components", {}).get("schemas", {})
    changed_existing_schemas = sorted(
        name
        for name in before_schemas.keys() & generated_schemas.keys()
        if before_schemas[name] != generated_schemas[name]
    )
    removed_schemas = sorted(before_schemas.keys() - generated_schemas.keys())
    if changed_existing_schemas or removed_schemas:
        raise SystemExit(
            "Global API must remain additive over the composed 0.19 contract; "
            f"changed={changed_existing_schemas}, removed={removed_schemas}"
        )

    before_paths = before.get("paths", {})
    generated_paths = generated.get("paths", {})
    changed_existing_paths = sorted(
        path
        for path in before_paths.keys() & generated_paths.keys()
        if before_paths[path] != generated_paths[path]
    )
    removed_paths = sorted(before_paths.keys() - generated_paths.keys())
    if changed_existing_paths or removed_paths:
        raise SystemExit(
            "Global API must remain additive over the composed 0.19 contract; "
            f"changed={changed_existing_paths}, removed={removed_paths}"
        )

    new_schema_names = sorted(generated_schemas.keys() - before_schemas.keys())
    new_path_names = sorted(generated_paths.keys() - before_paths.keys())
    return {
        "target_version": "0.20.0",
        "components": {
            "schemas": {name: generated_schemas[name] for name in new_schema_names}
        },
        "paths": {path: generated_paths[path] for path in new_path_names},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate additive KEFE OpenAPI 0.20 overlay")
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
            raise SystemExit("Checked-in OpenAPI 0.20 overlay is missing")
        try:
            checked = json.loads(args.output.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit("Checked-in OpenAPI 0.20 overlay is invalid JSON") from exc
        if checked != overlay:
            raise SystemExit("Checked-in OpenAPI 0.20 overlay is stale")
        print(f"OpenAPI 0.20 overlay matches {args.output}")
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(f"OpenAPI 0.20 overlay written to {args.output}")


if __name__ == "__main__":
    main()

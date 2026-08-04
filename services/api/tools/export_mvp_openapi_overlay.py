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
NON_MVP_ADDITIVE_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-case-builder.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-editorial-quality-review.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-flow-composer.v0.19.overlay.json",
)


def _load_non_mvp_additive_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for overlay_path in NON_MVP_ADDITIVE_OVERLAYS:
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        _merge_overlay(expected, overlay, overlay_path.name)
    return expected


def _build_mvp_runtime_openapi() -> dict[str, object]:
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
    before = _load_non_mvp_additive_contract()
    generated = _build_mvp_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.19.0":
        raise SystemExit("MVP OpenAPI overlay generator expects runtime API version 0.19.0")

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
            "MVP API must remain additive over the composed non-MVP contract; "
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
            "MVP API must remain additive over the composed non-MVP contract; "
            f"changed={changed_existing_paths}, removed={removed_paths}"
        )

    new_schema_names = sorted(generated_schemas.keys() - before_schemas.keys())
    new_path_names = sorted(generated_paths.keys() - before_paths.keys())
    return {
        "target_version": "0.19.0",
        "components": {"schemas": {name: generated_schemas[name] for name in new_schema_names}},
        "paths": {path: generated_paths[path] for path in new_path_names},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate additive KEFE OpenAPI 0.19 overlay")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = (
        json.dumps(
            build_overlay(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Checked-in OpenAPI 0.19 overlay is stale or missing")
        print(f"OpenAPI 0.19 overlay matches {args.output}")
        return
    args.output.write_text(rendered, encoding="utf-8")
    print(f"OpenAPI 0.19 overlay written to {args.output}")


if __name__ == "__main__":
    main()

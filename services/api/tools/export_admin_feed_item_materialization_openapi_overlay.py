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
BEFORE_MATERIALIZATION_OVERLAYS = (
    CONTRACTS / "openapi-consensus.v0.18.overlay.json",
    CONTRACTS / "openapi-mvp.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
    CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
)


def _load_before_materialization_contract() -> dict[str, object]:
    expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for path in BEFORE_MATERIALIZATION_OVERLAYS:
        _merge_overlay(
            expected,
            json.loads(path.read_text(encoding="utf-8")),
            path.name,
        )
    return expected


def _build_materialization_runtime_openapi() -> dict[str, object]:
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
    before = _load_before_materialization_contract()
    generated = _build_materialization_runtime_openapi()
    if generated.get("info", {}).get("version") != "0.19.0":
        raise SystemExit(
            "Admin Feed Item materialization overlay generator expects "
            "runtime API version 0.19.0"
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
            "Admin Feed Item materialization API must remain additive; "
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
            "Admin Feed Item materialization API must remain additive; "
            f"changed={changed_paths}, removed={removed_paths}"
        )

    new_schema_names = sorted(generated_schemas.keys() - before_schemas.keys())
    new_path_names = sorted(generated_paths.keys() - before_paths.keys())
    expected_schema_names = {
        "FeedItemMaterializationRequest",
        "FeedItemMaterializationResponse",
    }
    expected_path_names = {
        "/internal/admin/v1/feed-item-proposals/{proposal_id}/materialization"
    }
    if set(new_schema_names) != expected_schema_names:
        raise SystemExit(
            "Admin Feed Item materialization schema surface drifted: "
            f"{new_schema_names}"
        )
    if set(new_path_names) != expected_path_names:
        raise SystemExit(
            "Admin Feed Item materialization path surface drifted: "
            f"{new_path_names}"
        )
    return {
        "target_version": "0.19.0",
        "components": {
            "schemas": {name: generated_schemas[name] for name in new_schema_names}
        },
        "paths": {path: generated_paths[path] for path in new_path_names},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate additive Admin Feed Item materialization OpenAPI overlay"
        )
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
            raise SystemExit(
                "Checked-in Admin Feed Item materialization OpenAPI overlay is missing"
            )
        try:
            checked = json.loads(args.output.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(
                "Checked-in Admin Feed Item materialization OpenAPI overlay is invalid JSON"
            ) from exc
        if checked != overlay:
            raise SystemExit(
                "Checked-in Admin Feed Item materialization OpenAPI overlay is stale"
            )
        print(
            "Admin Feed Item materialization OpenAPI overlay matches "
            f"{args.output}"
        )
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(
        "Admin Feed Item materialization OpenAPI overlay written to "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()

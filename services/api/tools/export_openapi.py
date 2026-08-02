from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from kefe_api.main import create_app

OPENAPI_OVERLAYS = (
    "openapi-consensus.v0.18.overlay.json",
    "openapi-mvp.v0.19.overlay.json",
    "openapi-admin-projection.v0.19.overlay.json",
    "openapi-admin-proposal-queue.v0.19.overlay.json",
)


def build_openapi() -> dict[str, object]:
    return create_app().openapi()


def render_openapi() -> str:
    return json.dumps(build_openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _merge_overlay(expected: dict[str, object], overlay: dict[str, object], name: str) -> None:
    target_version = overlay.get("target_version")
    if not isinstance(target_version, str) or not target_version:
        raise SystemExit(f"OpenAPI overlay {name} requires target_version")
    expected.setdefault("info", {})["version"] = target_version

    expected_schemas = expected.setdefault("components", {}).setdefault("schemas", {})
    for schema_name, schema in overlay.get("components", {}).get("schemas", {}).items():
        if schema_name in expected_schemas:
            raise SystemExit(f"OpenAPI overlay schema collides before {name}: {schema_name}")
        expected_schemas[schema_name] = schema

    expected_paths = expected.setdefault("paths", {})
    for path, path_item in overlay.get("paths", {}).items():
        if path in expected_paths:
            raise SystemExit(f"OpenAPI overlay path collides before {name}: {path}")
        expected_paths[path] = path_item


def load_expected_contract(base_path: Path) -> dict[str, object]:
    """Compose the stable base snapshot with ordered reviewable additive overlays."""

    base = json.loads(base_path.read_text(encoding="utf-8"))
    expected = deepcopy(base)
    for overlay_name in OPENAPI_OVERLAYS:
        overlay_path = base_path.with_name(overlay_name)
        if not overlay_path.exists():
            continue
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        _merge_overlay(expected, overlay, overlay_name)
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description="Export/check deterministic KEFE OpenAPI JSON")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()

    if args.output is None and args.check is None:
        parser.error("at least one of --output or --check is required")

    generated = build_openapi()
    if args.output is not None:
        args.output.write_text(
            json.dumps(generated, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"OpenAPI written to {args.output}")

    if args.check is not None:
        committed = load_expected_contract(args.check)
        if committed != generated:
            raise SystemExit(
                "Generated OpenAPI differs from composed checked-in contract; "
                "regenerate/review the base snapshot or additive overlays"
            )
        print(f"OpenAPI contract matches composed contract rooted at {args.check}")


if __name__ == "__main__":
    main()

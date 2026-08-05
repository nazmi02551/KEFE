from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app

TARGET_VERSION = "0.19.0"
TARGET_PATHS = ("/v1/me", "/v1/me/privacy-export")


def _runtime() -> dict[str, Any]:
    previous = os.environ.get("KEFE_API_VERSION")
    os.environ["KEFE_API_VERSION"] = TARGET_VERSION
    get_settings.cache_clear()
    try:
        return create_app().openapi()
    finally:
        if previous is None:
            os.environ.pop("KEFE_API_VERSION", None)
        else:
            os.environ["KEFE_API_VERSION"] = previous
        get_settings.cache_clear()


def _schema_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            refs.add(ref.rsplit("/", 1)[-1])
        for child in value.values():
            refs.update(_schema_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_schema_refs(child))
    return refs


def build_focused(runtime: dict[str, Any]) -> dict[str, Any]:
    paths = {path: runtime["paths"][path] for path in TARGET_PATHS}
    schemas = runtime.get("components", {}).get("schemas", {})
    referenced = _schema_refs(paths)
    pending = list(referenced)
    while pending:
        name = pending.pop()
        nested = _schema_refs(schemas[name]) - referenced
        referenced.update(nested)
        pending.extend(nested)
    return {
        "target_version": TARGET_VERSION,
        "components": {"schemas": {name: schemas[name] for name in sorted(referenced)}},
        "paths": paths,
    }


def render(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + chr(10)


def update_base(runtime: dict[str, Any], base_path: Path) -> None:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    focused = build_focused(runtime)
    for path, path_item in focused["paths"].items():
        base.setdefault("paths", {})[path] = path_item
    base_schemas = base.setdefault("components", {}).setdefault("schemas", {})
    for name, schema in focused["components"]["schemas"].items():
        base_schemas[name] = schema
    base_path.write_text(render(base), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export exact privacy self-service OpenAPI")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--update-base", type=Path)
    args = parser.parse_args()

    runtime = _runtime()
    focused = build_focused(runtime)
    rendered = render(focused)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Focused privacy OpenAPI contract is stale or missing")
        print(f"Focused privacy OpenAPI matches {args.output}")
    else:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Focused privacy OpenAPI written to {args.output}")
    if args.update_base is not None:
        update_base(runtime, args.update_base)
        print(f"Privacy paths and schemas updated in {args.update_base}")


if __name__ == "__main__":
    main()

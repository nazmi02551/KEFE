from __future__ import annotations

import argparse
import json
from pathlib import Path

from kefe_api.main import create_app


def build_openapi() -> dict[str, object]:
    return create_app().openapi()


def render_openapi() -> str:
    return json.dumps(build_openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


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
        committed = json.loads(args.check.read_text(encoding="utf-8"))
        if committed != generated:
            raise SystemExit(
                "Generated OpenAPI differs from checked-in contract; regenerate and review compatibility"
            )
        print(f"OpenAPI contract matches {args.check}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kefe_api.main import create_app


def render_openapi() -> str:
    document = create_app().openapi()
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export deterministic KEFE OpenAPI JSON")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render_openapi(), encoding="utf-8")
    print(f"OpenAPI written to {args.output}")


if __name__ == "__main__":
    main()

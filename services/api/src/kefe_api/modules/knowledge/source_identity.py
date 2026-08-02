from __future__ import annotations

import re

_VERSIONED_ADAPTER_CODE = re.compile(
    r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*\.v[1-9][0-9]*$"
)


def require_versioned_adapter_code(adapter_code: str) -> None:
    if not adapter_code.strip():
        raise ValueError("adapter_code must not be blank")
    if _VERSIONED_ADAPTER_CODE.fullmatch(adapter_code) is None:
        raise ValueError(
            "adapter_code must be an immutable versioned identifier ending in .vN"
        )

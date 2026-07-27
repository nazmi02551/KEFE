from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DomainError(Exception):
    code: str
    title: str
    status_code: int
    detail: str | None = None
    retryable: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.detail or self.title

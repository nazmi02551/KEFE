from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    event_name: str
    event_version: int
    occurred_at: datetime
    payload: dict[str, Any]
    attempts: int


@dataclass(frozen=True, slots=True)
class PublishResult:
    claimed: int
    published: int
    failed: int
    dead_lettered: int

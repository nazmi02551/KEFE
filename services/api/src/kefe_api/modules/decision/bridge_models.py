from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BridgeArgumentItem:
    bridge_id: UUID
    case_version_id: UUID
    synthesis_thesis: str
    connecting_values: tuple[str, ...]
    cross_group_support_rate: float
    sample_size: int
    created_at: datetime

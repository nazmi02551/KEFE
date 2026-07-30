from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PrivacyExport:
    actor_id: UUID
    actor_kind: str
    generated_at: datetime
    retention: dict[str, Any]
    product_data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PrivacyDeletionReceipt:
    receipt_id: UUID
    actor_id: UUID
    actor_kind: str
    deleted_at: datetime
    private_data_deleted: bool
    aggregate_contributions_anonymized: bool
    policy_version: str

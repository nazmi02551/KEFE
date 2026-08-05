from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PrivacyExportManifest:
    dataset_counts: dict[str, int]
    total_records: int
    empty_datasets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PrivacyExport:
    schema_version: str
    actor_id: UUID
    actor_kind: str
    generated_at: datetime
    retention: dict[str, Any]
    manifest: PrivacyExportManifest
    product_data: dict[str, Any]
    data_sha256: str


@dataclass(frozen=True, slots=True)
class PrivacyDeletionReceipt:
    receipt_id: UUID
    actor_id: UUID
    actor_kind: str
    deleted_at: datetime
    private_data_deleted: bool
    aggregate_contributions_anonymized: bool
    policy_version: str

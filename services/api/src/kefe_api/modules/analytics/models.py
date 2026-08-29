from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class AnalyticsPrivacyClass(StrEnum):
    PRODUCT_ANALYTICS = "PRODUCT_ANALYTICS"
    TRUST_AND_SAFETY = "TRUST_AND_SAFETY"
    OPERATIONS_FINOPS = "OPERATIONS_FINOPS"


class AnalyticsRetentionClass(StrEnum):
    STANDARD_13_MONTHS = "STANDARD_13_MONTHS"
    EXTENDED_24_MONTHS = "EXTENDED_24_MONTHS"


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    id: UUID
    source_event_id: UUID
    source_event_name: str
    source_event_version: int
    analytics_name: str
    analytics_version: int
    occurred_at: datetime
    producer_version: str
    actor_id: UUID | None
    session_id: UUID
    case_version_id: UUID | None
    contribution_class: str | None
    privacy_class: AnalyticsPrivacyClass
    retention_class: AnalyticsRetentionClass
    metric_families: tuple[str, ...]
    payload: dict[str, Any]

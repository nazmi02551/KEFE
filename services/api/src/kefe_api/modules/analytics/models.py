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


@dataclass(frozen=True, slots=True)
class ActivationJourney:
    session_id: UUID
    actor_id: UUID | None
    case_version_id: UUID
    started_at: datetime | None
    started_source_event_id: UUID | None
    committed_at: datetime | None
    committed_source_event_id: UUID | None
    result_revealed_at: datetime | None
    result_revealed_source_event_id: UUID | None


@dataclass(frozen=True, slots=True)
class QualityJourney:
    session_id: UUID
    case_version_id: UUID | None
    committed_at: datetime | None
    committed_source_event_id: UUID | None
    perspective_viewed_at: datetime | None
    perspective_viewed_source_event_id: UUID | None
    exposure_recorded_at: datetime | None
    exposure_recorded_source_event_id: UUID | None
    intervention_exposed_at: datetime | None
    intervention_exposed_source_event_id: UUID | None
    decision_revised_at: datetime | None
    decision_revised_source_event_id: UUID | None

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType

from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthSnapshot,
)
from kefe_api.modules.identity.otp_delivery_health import (
    OtpDeliveryHealthPolicy,
    OtpDeliveryHealthSnapshot,
)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


class AdminOperationalSignal(StrEnum):
    QUIET = "QUIET"
    NOMINAL = "NOMINAL"
    ATTENTION = "ATTENTION"
    CRITICAL = "CRITICAL"


class AdminOperationalReason(StrEnum):
    CONTENT_SUPPLY_ATTENTION = "CONTENT_SUPPLY_ATTENTION"
    CONTENT_SUPPLY_CRITICAL = "CONTENT_SUPPLY_CRITICAL"
    EDITORIAL_IN_REVIEW_BACKLOG = "EDITORIAL_IN_REVIEW_BACKLOG"
    PROPOSAL_REVIEW_BACKLOG = "PROPOSAL_REVIEW_BACKLOG"
    MODERATION_BACKLOG = "MODERATION_BACKLOG"
    OTP_DELIVERY_ATTENTION = "OTP_DELIVERY_ATTENTION"
    OTP_DELIVERY_CRITICAL = "OTP_DELIVERY_CRITICAL"


@dataclass(frozen=True, slots=True)
class AdminOperationalReportPolicy:
    in_review_attention_threshold: int = 50
    pending_proposal_attention_threshold: int = 100
    moderation_candidate_attention_threshold: int = 50
    content_supply: ContentSupplyHealthPolicy = field(default_factory=ContentSupplyHealthPolicy)
    otp_delivery: OtpDeliveryHealthPolicy = field(default_factory=OtpDeliveryHealthPolicy)

    def __post_init__(self) -> None:
        for value, name in (
            (self.in_review_attention_threshold, "in_review_attention_threshold"),
            (
                self.pending_proposal_attention_threshold,
                "pending_proposal_attention_threshold",
            ),
            (
                self.moderation_candidate_attention_threshold,
                "moderation_candidate_attention_threshold",
            ),
        ):
            if value < 0 or value > 1_000_000:
                raise ValueError(f"{name} is outside the supported range")


@dataclass(frozen=True, slots=True)
class AdminOperationalReportSnapshot:
    as_of: datetime
    overall_signal: AdminOperationalSignal
    reason_codes: tuple[str, ...]
    policy: AdminOperationalReportPolicy
    content_supply: ContentSupplyHealthSnapshot
    otp_delivery: OtpDeliveryHealthSnapshot
    editorial_lifecycle: Mapping[str, int]
    proposal_review: Mapping[str, int]
    moderation: Mapping[str, int]

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        if self.content_supply.as_of != self.as_of:
            raise ValueError("content supply snapshot must share report as_of")
        if self.otp_delivery.as_of != self.as_of:
            raise ValueError("OTP delivery snapshot must share report as_of")
        if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("reason_codes must be sorted and unique")
        for section in (
            self.editorial_lifecycle,
            self.proposal_review,
            self.moderation,
        ):
            if any(value < 0 for value in section.values()):
                raise ValueError("operational report counts must be non-negative")

    @staticmethod
    def immutable_counts(values: dict[str, int]) -> Mapping[str, int]:
        return MappingProxyType(dict(values))

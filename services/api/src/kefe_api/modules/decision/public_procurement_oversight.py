from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProcurementIntegrityLevel(StrEnum):
    OPEN_COMPETITIVE_VERIFIED = "OPEN_COMPETITIVE_VERIFIED"
    ANOMALOUS_SOLE_SOURCE_REVIEW = "ANOMALOUS_SOLE_SOURCE_REVIEW"
    CRITICAL_OVERRUN_ALERT = "CRITICAL_OVERRUN_ALERT"


@dataclass(frozen=True, slots=True)
class ProcurementOversightResult:
    tender_id: str
    contracting_authority: str
    integrity_level: ProcurementIntegrityLevel
    awarded_amount_try: float
    cost_overrun_pct: float
    active_civic_auditors_count: int


class PublicProcurementOversightService:
    @staticmethod
    def audit_tender(
        *,
        tender_id: str,
        contracting_authority: str,
        awarded_amount_try: float,
        cost_overrun_pct: float,
        active_civic_auditors_count: int,
    ) -> ProcurementOversightResult:
        if awarded_amount_try < 0:
            raise ValueError("awarded_amount_try cannot be negative")
        if cost_overrun_pct < 0:
            raise ValueError("cost_overrun_pct cannot be negative")
        if active_civic_auditors_count < 0:
            raise ValueError("active_civic_auditors_count cannot be negative")
        if len(contracting_authority.strip()) < 3:
            raise ValueError("contracting_authority must have at least 3 characters")

        if cost_overrun_pct > 0.25:
            level = ProcurementIntegrityLevel.CRITICAL_OVERRUN_ALERT
        elif cost_overrun_pct > 0.05:
            level = ProcurementIntegrityLevel.ANOMALOUS_SOLE_SOURCE_REVIEW
        else:
            level = ProcurementIntegrityLevel.OPEN_COMPETITIVE_VERIFIED

        return ProcurementOversightResult(
            tender_id=tender_id.strip(),
            contracting_authority=contracting_authority.strip(),
            integrity_level=level,
            awarded_amount_try=round(awarded_amount_try, 2),
            cost_overrun_pct=round(cost_overrun_pct, 2),
            active_civic_auditors_count=active_civic_auditors_count,
        )

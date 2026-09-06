from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import hashlib
from typing import Sequence
from uuid import UUID


class JurisdictionLevel(str, Enum):
    MUNICIPAL = "MUNICIPAL"
    REGIONAL = "REGIONAL"
    NATIONAL = "NATIONAL"
    TRANSNATIONAL = "TRANSNATIONAL"


class ScopeAlignmentStatus(str, Enum):
    STRICTLY_ALIGNED = "STRICTLY_ALIGNED"
    OVERBROAD_WARNING = "OVERBROAD_WARNING"
    MISMATCH_DISQUALIFIED = "MISMATCH_DISQUALIFIED"


@dataclass(frozen=True)
class ScopeDimensionResult:
    dimension: str
    declared_scope: str
    sample_scope: str
    alignment_score: float
    is_valid: bool


@dataclass(frozen=True)
class SignalScopeAlignmentReport:
    signal_id: UUID
    case_version_id: UUID
    jurisdiction_level: JurisdictionLevel
    target_population: str
    geographic_scope: str
    alignment_status: ScopeAlignmentStatus
    overall_alignment_score: float
    dimensions: Sequence[ScopeDimensionResult]
    validity_window_days: int
    certified_at: datetime
    scope_seal_hash: str


class SignalScopeAlignmentService:
    """Enforces constitutional boundary limits preventing signals from silently broadening beyond measured scope."""

    @staticmethod
    def evaluate(
        *,
        signal_id: UUID,
        case_version_id: UUID,
        jurisdiction_level: JurisdictionLevel = JurisdictionLevel.MUNICIPAL,
        target_population: str = "Kent İçi Raylı Sistem Yolcuları",
        geographic_scope: str = "İstanbul / Türkiye",
        validity_window_days: int = 90,
        jurisdiction_score: float = 0.96,
        geographic_score: float = 0.92,
        demographic_score: float = 0.88,
        temporal_score: float = 0.95,
        certified_at: datetime | None = None,
    ) -> SignalScopeAlignmentReport:
        if certified_at is None:
            certified_at = datetime.now(UTC)

        d_jur = ScopeDimensionResult(
            dimension="JURISDICTION",
            declared_scope=jurisdiction_level.value,
            sample_scope=f"Local Constituency ({jurisdiction_level.value})",
            alignment_score=round(jurisdiction_score, 4),
            is_valid=jurisdiction_score >= 0.80,
        )

        d_geo = ScopeDimensionResult(
            dimension="GEOGRAPHIC",
            declared_scope=geographic_scope,
            sample_scope=geographic_scope,
            alignment_score=round(geographic_score, 4),
            is_valid=geographic_score >= 0.80,
        )

        d_demo = ScopeDimensionResult(
            dimension="DEMOGRAPHIC_TARGET",
            declared_scope=target_population,
            sample_scope=f"Verified {target_population} Deliberators",
            alignment_score=round(demographic_score, 4),
            is_valid=demographic_score >= 0.75,
        )

        d_temp = ScopeDimensionResult(
            dimension="TEMPORAL_WINDOW",
            declared_scope=f"{validity_window_days} Days Binding Window",
            sample_scope="Active Freshness Interval",
            alignment_score=round(temporal_score, 4),
            is_valid=temporal_score >= 0.70,
        )

        dimensions = [d_jur, d_geo, d_demo, d_temp]

        overall_score = round(
            (d_jur.alignment_score * 0.30)
            + (d_geo.alignment_score * 0.25)
            + (d_demo.alignment_score * 0.25)
            + (d_temp.alignment_score * 0.20),
            4,
        )

        if overall_score >= 0.85 and all(d.is_valid for d in dimensions):
            status = ScopeAlignmentStatus.STRICTLY_ALIGNED
        elif overall_score >= 0.70:
            status = ScopeAlignmentStatus.OVERBROAD_WARNING
        else:
            status = ScopeAlignmentStatus.MISMATCH_DISQUALIFIED

        seal_payload = (
            f"{signal_id}:{case_version_id}:{jurisdiction_level.value}:"
            f"{geographic_scope}:{overall_score:.4f}:{status.value}:{certified_at.isoformat()}"
        )
        scope_seal_hash = hashlib.sha256(seal_payload.encode("utf-8")).hexdigest()

        return SignalScopeAlignmentReport(
            signal_id=signal_id,
            case_version_id=case_version_id,
            jurisdiction_level=jurisdiction_level,
            target_population=target_population,
            geographic_scope=geographic_scope,
            alignment_status=status,
            overall_alignment_score=overall_score,
            dimensions=dimensions,
            validity_window_days=validity_window_days,
            certified_at=certified_at,
            scope_seal_hash=scope_seal_hash,
        )

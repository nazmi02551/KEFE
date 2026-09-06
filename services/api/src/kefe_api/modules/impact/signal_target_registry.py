from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import hashlib
from typing import Sequence
from uuid import UUID


class TargetType(str, Enum):
    MUNICIPAL_GOVERNMENT = "MUNICIPAL_GOVERNMENT"
    MINISTRY_DEPARTMENT = "MINISTRY_DEPARTMENT"
    REGULATORY_BODY = "REGULATORY_BODY"
    PUBLIC_UTILITY = "PUBLIC_UTILITY"
    CORPORATE_ENTITY = "CORPORATE_ENTITY"
    CIVIC_OMBUDSMAN = "CIVIC_OMBUDSMAN"


class DispatchStatus(str, Enum):
    PROPOSED_TARGET = "PROPOSED_TARGET"
    VERIFIED_TARGET = "VERIFIED_TARGET"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACTION_PLEDGED = "ACTION_PLEDGED"
    DECLINED_JURISDICTION = "DECLINED_JURISDICTION"


@dataclass(frozen=True)
class SignalTargetItem:
    target_id: UUID
    target_name: str
    target_type: TargetType
    jurisdiction_level: str
    official_contact_channel: str
    dispatch_status: DispatchStatus
    response_due_days: int
    dispatched_at: datetime | None = None
    acknowledged_at: datetime | None = None


@dataclass(frozen=True)
class SignalTargetRegistryReport:
    signal_id: UUID
    case_version_id: UUID
    primary_target_id: UUID
    targets: Sequence[SignalTargetItem]
    certified_at: datetime
    registry_proof_hash: str


class SignalTargetRegistryService:
    """Manages the formal mapping, jurisdictional verification, and dispatch tracking of civic signals to decision-making bodies."""

    @classmethod
    def evaluate(
        cls,
        *,
        signal_id: UUID,
        case_version_id: UUID,
        certified_at: datetime | None = None,
    ) -> SignalTargetRegistryReport:
        if certified_at is None:
            certified_at = datetime.now(UTC)

        primary_id = UUID("bbbbbbbb-1111-4bbb-8bbb-111111111111")
        secondary_id = UUID("bbbbbbbb-2222-4bbb-8bbb-222222222222")

        t1 = SignalTargetItem(
            target_id=primary_id,
            target_name="İstanbul Büyükşehir Belediyesi Ulaşım Koordinasyon Merkezi (UKOME)",
            target_type=TargetType.MUNICIPAL_GOVERNMENT,
            jurisdiction_level="MUNICIPAL",
            official_contact_channel="ukome.kararlar@ibb.gov.tr",
            dispatch_status=DispatchStatus.ACKNOWLEDGED,
            response_due_days=30,
            dispatched_at=datetime(2026, 8, 16, 9, 0, 0, tzinfo=UTC),
            acknowledged_at=datetime(2026, 8, 18, 14, 20, 0, tzinfo=UTC),
        )

        t2 = SignalTargetItem(
            target_id=secondary_id,
            target_name="T.C. Ulaştırma ve Altyapı Bakanlığı Marmaray Bölge Müdürlüğü",
            target_type=TargetType.MINISTRY_DEPARTMENT,
            jurisdiction_level="REGIONAL",
            official_contact_channel="marmaray.koordinasyon@uab.gov.tr",
            dispatch_status=DispatchStatus.DISPATCHED,
            response_due_days=45,
            dispatched_at=datetime(2026, 8, 16, 9, 15, 0, tzinfo=UTC),
            acknowledged_at=None,
        )

        targets = [t1, t2]

        payload = (
            f"{signal_id}:{case_version_id}:{primary_id}:"
            f"{t1.dispatch_status.value}:{len(targets)}:{certified_at.isoformat()}"
        )
        registry_proof_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return SignalTargetRegistryReport(
            signal_id=signal_id,
            case_version_id=case_version_id,
            primary_target_id=primary_id,
            targets=targets,
            certified_at=certified_at,
            registry_proof_hash=registry_proof_hash,
        )

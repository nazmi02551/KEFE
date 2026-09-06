from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SignalConfidenceTier(StrEnum):
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"


@dataclass(frozen=True, slots=True)
class SignalConsensusCardItem:
    signal_id: UUID
    case_version_id: UUID
    case_title: str
    consensus_statement: str
    agreement_percentage: float
    sample_size: int
    confidence_tier: SignalConfidenceTier
    certified_at: datetime

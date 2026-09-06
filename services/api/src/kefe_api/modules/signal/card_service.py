from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.card_models import (
    SignalConfidenceTier,
    SignalConsensusCardItem,
)


class SignalConsensusCardService:
    @staticmethod
    def compose_card(
        *,
        signal_id: UUID,
        case_version_id: UUID,
        case_title: str,
        consensus_statement: str,
        agreement_percentage: float,
        sample_size: int,
        certified_at: datetime | None = None,
    ) -> SignalConsensusCardItem:
        if sample_size < 100:
            raise ValueError("sample_size must be >= 100 to qualify for a Signal Consensus Card")

        if not (0.0 <= agreement_percentage <= 100.0):
            raise ValueError("agreement_percentage must be between 0.0 and 100.0")

        if sample_size >= 1000 and agreement_percentage >= 75.0:
            tier = SignalConfidenceTier.GOLD
        elif sample_size >= 500 and agreement_percentage >= 65.0:
            tier = SignalConfidenceTier.SILVER
        else:
            tier = SignalConfidenceTier.BRONZE

        return SignalConsensusCardItem(
            signal_id=signal_id,
            case_version_id=case_version_id,
            case_title=case_title.strip(),
            consensus_statement=consensus_statement.strip(),
            agreement_percentage=round(agreement_percentage, 2),
            sample_size=sample_size,
            confidence_tier=tier,
            certified_at=certified_at or datetime.now(UTC),
        )

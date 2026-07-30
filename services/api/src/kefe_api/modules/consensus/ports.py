from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.consensus.models import (
    ConsensusAggregate,
    ConsensusCardVersion,
    ConsensusParticipation,
    ConsensusParticipationAttempt,
)


class ConsensusRepository(Protocol):
    def list_cards(self, case_version_id: UUID) -> tuple[ConsensusCardVersion, ...]: ...

    def get_card(
        self,
        *,
        case_version_id: UUID,
        card_version_id: UUID,
    ) -> ConsensusCardVersion | None: ...

    def get_participation(
        self,
        *,
        actor_id: UUID,
        card_version_id: UUID,
    ) -> ConsensusParticipation | None: ...

    def create_participation(
        self,
        *,
        participation: ConsensusParticipation,
    ) -> ConsensusParticipationAttempt: ...

    def aggregate(
        self,
        *,
        card: ConsensusCardVersion,
        contribution_class: str,
        generated_at: datetime,
    ) -> ConsensusAggregate: ...

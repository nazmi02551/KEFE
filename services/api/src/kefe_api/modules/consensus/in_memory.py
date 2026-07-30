from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.consensus.models import (
    ConsensusAggregate,
    ConsensusCardVersion,
    ConsensusContributionClass,
    ConsensusParticipation,
    ConsensusParticipationAttempt,
    ConsensusParticipationStatus,
)


class InMemoryConsensusRepository:
    def __init__(self, cards: tuple[ConsensusCardVersion, ...] = ()) -> None:
        self._versions = {card.id: card for card in cards}
        self._published_by_card = {card.card_id: card for card in cards}
        self._participations_by_actor_card_version: dict[
            tuple[UUID, UUID], ConsensusParticipation
        ] = {}
        self._participations_by_actor_idempotency: dict[
            tuple[UUID, str], ConsensusParticipation
        ] = {}

    def list_cards(self, case_version_id: UUID) -> tuple[ConsensusCardVersion, ...]:
        return tuple(
            sorted(
                (
                    card
                    for card in self._published_by_card.values()
                    if card.case_version_id == case_version_id
                ),
                key=lambda card: (card.published_at, str(card.card_id)),
            )
        )

    def get_card(
        self,
        *,
        case_version_id: UUID,
        card_id: UUID,
    ) -> ConsensusCardVersion | None:
        card = self._published_by_card.get(card_id)
        if card is None or card.case_version_id != case_version_id:
            return None
        return card

    def get_participation(
        self,
        *,
        actor_id: UUID,
        card_version_id: UUID,
    ) -> ConsensusParticipation | None:
        return self._participations_by_actor_card_version.get(
            (actor_id, card_version_id)
        )

    def create_participation(
        self,
        *,
        participation: ConsensusParticipation,
    ) -> ConsensusParticipationAttempt:
        replay = self._participations_by_actor_idempotency.get(
            (participation.actor_id, participation.idempotency_key)
        )
        if replay is not None:
            if replay.card_version_id == participation.card_version_id:
                return ConsensusParticipationAttempt(
                    ConsensusParticipationStatus.IDEMPOTENT_REPLAY,
                    replay,
                )
            return ConsensusParticipationAttempt(
                ConsensusParticipationStatus.IDEMPOTENCY_KEY_REUSED,
                replay,
            )

        existing = self._participations_by_actor_card_version.get(
            (participation.actor_id, participation.card_version_id)
        )
        if existing is not None:
            return ConsensusParticipationAttempt(
                ConsensusParticipationStatus.ALREADY_PARTICIPATED,
                existing,
            )

        self._participations_by_actor_card_version[
            (participation.actor_id, participation.card_version_id)
        ] = participation
        self._participations_by_actor_idempotency[
            (participation.actor_id, participation.idempotency_key)
        ] = participation
        return ConsensusParticipationAttempt(
            ConsensusParticipationStatus.CREATED,
            participation,
        )

    def aggregate(
        self,
        *,
        card: ConsensusCardVersion,
        contribution_class: str,
        generated_at: datetime,
    ) -> ConsensusAggregate:
        rows = tuple(
            participation
            for participation in self._participations_by_actor_card_version.values()
            if participation.card_version_id == card.id
            and participation.contribution_class == contribution_class
        )
        sample_size = len(rows)
        stance_counts = Counter(row.stance_code for row in rows)
        reason_counts: Counter[str] = Counter()
        for row in rows:
            reason_counts.update(set(row.reason_tag_codes))

        divisor = sample_size if sample_size > 0 else 1
        stance_distribution = {
            code: stance_counts.get(code, 0) / divisor for code in card.stance_codes
        }
        reason_distribution = {
            code: reason_counts.get(code, 0) / divisor
            for code in card.reason_tag_codes
            if reason_counts.get(code, 0) > 0
        }
        return ConsensusAggregate.create(
            card_version_id=card.id,
            case_version_id=card.case_version_id,
            contribution_class=contribution_class,
            sample_size=sample_size,
            stance_distribution=stance_distribution,
            reason_pattern_distribution=reason_distribution,
            methodology_version=card.methodology_version,
            generated_at=generated_at,
            provenance_note=(
                "Post-commit EXPOSED Consensus sample. It is descriptive WE data and "
                "is not pooled into the core pre-result result or a Signal."
            ),
        )


DEMO_CONSENSUS_CARD_ID = UUID("91000000-0000-4000-8000-000000000001")
DEMO_CONSENSUS_CARD_VERSION_ID = UUID("91000000-0000-4000-8000-000000000101")
DEMO_CONSENSUS_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")


def build_demo_consensus_repository() -> InMemoryConsensusRepository:
    return InMemoryConsensusRepository(
        cards=(
            ConsensusCardVersion(
                id=DEMO_CONSENSUS_CARD_VERSION_ID,
                card_id=DEMO_CONSENSUS_CARD_ID,
                version_no=1,
                case_version_id=DEMO_CONSENSUS_CASE_VERSION_ID,
                proposition=(
                    "Sınırlı bir kaynak dağıtılırken açıkça daha acil ihtiyaç, "
                    "salt sıra önceliğinden önce gelmelidir."
                ),
                stance_codes=("AGREE", "MIXED", "DISAGREE"),
                reason_tag_codes=(
                    "NEED",
                    "FAIRNESS",
                    "RULES",
                    "PRACTICAL_IMPACT",
                ),
                max_reason_tags=2,
                methodology_version="CONSENSUS_WE_V1",
                published_at=datetime(2026, 7, 30, tzinfo=UTC),
            ),
        )
    )


__all__ = [
    "DEMO_CONSENSUS_CARD_ID",
    "DEMO_CONSENSUS_CARD_VERSION_ID",
    "InMemoryConsensusRepository",
    "build_demo_consensus_repository",
    "ConsensusContributionClass",
]

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.consensus.models import (
    ConsensusCardView,
    ConsensusContributionClass,
    ConsensusParticipation,
    ConsensusParticipationStatus,
)
from kefe_api.modules.consensus.ports import ConsensusRepository
from kefe_api.modules.decision.models import WeighSession, WeighState
from kefe_api.modules.decision.ports import DecisionRepository


class ConsensusService:
    def __init__(
        self,
        *,
        consensus_repository: ConsensusRepository,
        decision_repository: DecisionRepository,
    ) -> None:
        self._consensus = consensus_repository
        self._decision = decision_repository

    def list_cards(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
    ) -> tuple[ConsensusCardView, ...]:
        session = self._committed_owned_session(actor_id, session_id)
        views: list[ConsensusCardView] = []
        for card in self._consensus.list_cards(session.case_version_id):
            participation = self._consensus.get_participation(
                actor_id=actor_id,
                card_version_id=card.id,
            )
            aggregate = None
            if participation is not None:
                aggregate = self._consensus.aggregate(
                    card=card,
                    contribution_class=participation.contribution_class,
                    generated_at=datetime.now(UTC),
                )
            views.append(
                ConsensusCardView(
                    card=card,
                    participation=participation,
                    aggregate=aggregate,
                )
            )

        self._decision.append_event(
            "consensus.card_viewed",
            session.id,
            {
                "case_version_id": str(session.case_version_id),
                "card_count": len(views),
                "participated_count": sum(
                    1 for view in views if view.participation is not None
                ),
            },
        )
        for view in views:
            if view.aggregate is not None:
                self._record_aggregate_viewed(session=session, view=view)
        return tuple(views)

    def participate(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        card_id: UUID,
        stance_code: str,
        reason_tag_codes: list[str],
        idempotency_key: str,
    ) -> ConsensusCardView:
        session = self._committed_owned_session(actor_id, session_id)
        card = self._consensus.get_card(
            case_version_id=session.case_version_id,
            card_id=card_id,
        )
        if card is None:
            raise DomainError(
                "CONSENSUS_CARD_NOT_FOUND",
                "Consensus card not found",
                404,
            )

        normalized_stance = stance_code.strip().upper()
        if normalized_stance not in card.stance_codes:
            raise DomainError(
                "CONSENSUS_STANCE_INVALID",
                "Consensus stance is not supported by this card",
                422,
            )

        normalized_tags = tuple(
            dict.fromkeys(
                tag.strip().upper() for tag in reason_tag_codes if tag.strip()
            )
        )
        unknown_tags = [
            tag for tag in normalized_tags if tag not in card.reason_tag_codes
        ]
        if unknown_tags:
            raise DomainError(
                "CONSENSUS_REASON_TAG_INVALID",
                "Consensus reason contains unsupported tags",
                422,
                meta={"unknown_tags": unknown_tags},
            )
        if len(normalized_tags) > card.max_reason_tags:
            raise DomainError(
                "CONSENSUS_REASON_TAG_LIMIT_EXCEEDED",
                "Too many Consensus reason tags",
                422,
                meta={"max_tags": card.max_reason_tags},
            )

        participation = ConsensusParticipation(
            id=uuid4(),
            card_version_id=card.id,
            session_id=session.id,
            actor_id=actor_id,
            case_version_id=session.case_version_id,
            stance_code=normalized_stance,
            reason_tag_codes=normalized_tags,
            contribution_class=ConsensusContributionClass.EXPOSED.value,
            idempotency_key=idempotency_key,
            participated_at=datetime.now(UTC),
        )
        attempt = self._consensus.create_participation(participation=participation)
        if attempt.status is ConsensusParticipationStatus.IDEMPOTENCY_KEY_REUSED:
            raise DomainError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key was already used for another Consensus participation",
                409,
            )
        if attempt.status is ConsensusParticipationStatus.ALREADY_PARTICIPATED:
            raise DomainError(
                "CONSENSUS_ALREADY_PARTICIPATED",
                "Consensus participation is immutable in this version",
                409,
            )
        if attempt.status not in {
            ConsensusParticipationStatus.CREATED,
            ConsensusParticipationStatus.IDEMPOTENT_REPLAY,
        }:
            raise RuntimeError(f"Unsupported Consensus participation status: {attempt.status}")
        assert attempt.participation is not None
        stored = attempt.participation

        aggregate = self._consensus.aggregate(
            card=card,
            contribution_class=stored.contribution_class,
            generated_at=datetime.now(UTC),
        )
        view = ConsensusCardView(
            card=card,
            participation=stored,
            aggregate=aggregate,
        )
        if attempt.status is ConsensusParticipationStatus.CREATED:
            self._decision.append_event(
                "consensus.participated",
                session.id,
                {
                    "case_version_id": str(session.case_version_id),
                    "card_id": str(card.card_id),
                    "card_version_id": str(card.id),
                    "stance_code": stored.stance_code,
                    "reason_tag_codes": list(stored.reason_tag_codes),
                    "reason_tag_count": len(stored.reason_tag_codes),
                    "contribution_class": stored.contribution_class,
                },
            )
        self._record_aggregate_viewed(session=session, view=view)
        return view

    def _record_aggregate_viewed(
        self,
        *,
        session: WeighSession,
        view: ConsensusCardView,
    ) -> None:
        aggregate = view.aggregate
        if aggregate is None:
            return
        self._decision.append_event(
            "consensus.aggregate_viewed",
            session.id,
            {
                "case_version_id": str(session.case_version_id),
                "card_id": str(view.card.card_id),
                "card_version_id": str(view.card.id),
                "sample_size": aggregate.sample_size,
                "contribution_class": aggregate.contribution_class,
                "methodology_version": aggregate.methodology_version,
            },
        )

    def _committed_owned_session(
        self,
        actor_id: UUID,
        session_id: UUID,
    ) -> WeighSession:
        session = self._decision.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError(
                "WEIGH_SESSION_NOT_FOUND",
                "Weigh session not found",
                404,
            )
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "CONSENSUS_COMMIT_REQUIRED",
                "Commit is required before Consensus participation",
                403,
            )
        return session

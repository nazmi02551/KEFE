from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.consensus.models import (
    ConsensusAggregate,
    ConsensusCardVersion,
    ConsensusParticipation,
    ConsensusParticipationAttempt,
    ConsensusParticipationStatus,
)


class PostgresConsensusRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_cards(self, case_version_id: UUID) -> tuple[ConsensusCardVersion, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        id, card_id, version_no, case_version_id, proposition,
                        stance_codes, reason_tag_codes, max_reason_tags,
                        methodology_version, published_at
                    FROM collective.consensus_card_version
                    WHERE case_version_id = :case_version_id
                      AND status = 'PUBLISHED'
                    ORDER BY published_at ASC, card_id ASC
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()
        return tuple(self._card(row) for row in rows)

    def get_card(
        self,
        *,
        case_version_id: UUID,
        card_id: UUID,
    ) -> ConsensusCardVersion | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        id, card_id, version_no, case_version_id, proposition,
                        stance_codes, reason_tag_codes, max_reason_tags,
                        methodology_version, published_at
                    FROM collective.consensus_card_version
                    WHERE card_id = :card_id
                      AND case_version_id = :case_version_id
                      AND status = 'PUBLISHED'
                    """
                ),
                {"card_id": card_id, "case_version_id": case_version_id},
            ).mappings().one_or_none()
        return None if row is None else self._card(row)

    def get_participation(
        self,
        *,
        actor_id: UUID,
        card_version_id: UUID,
    ) -> ConsensusParticipation | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(self._participation_select() + " WHERE actor_id = :actor_id AND card_version_id = :card_version_id"),
                {"actor_id": actor_id, "card_version_id": card_version_id},
            ).mappings().one_or_none()
        return None if row is None else self._participation(row)

    def _get_by_idempotency(
        self,
        *,
        actor_id: UUID,
        idempotency_key: str,
    ) -> ConsensusParticipation | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(self._participation_select() + " WHERE actor_id = :actor_id AND idempotency_key = :idempotency_key"),
                {"actor_id": actor_id, "idempotency_key": idempotency_key},
            ).mappings().one_or_none()
        return None if row is None else self._participation(row)

    def create_participation(
        self,
        *,
        participation: ConsensusParticipation,
    ) -> ConsensusParticipationAttempt:
        try:
            with self._engine.begin() as connection:
                replay = connection.execute(
                    text(
                        self._participation_select()
                        + " WHERE actor_id = :actor_id AND idempotency_key = :idempotency_key FOR UPDATE"
                    ),
                    {
                        "actor_id": participation.actor_id,
                        "idempotency_key": participation.idempotency_key,
                    },
                ).mappings().one_or_none()
                if replay is not None:
                    stored = self._participation(replay)
                    return ConsensusParticipationAttempt(
                        ConsensusParticipationStatus.IDEMPOTENT_REPLAY
                        if stored.card_version_id == participation.card_version_id
                        else ConsensusParticipationStatus.IDEMPOTENCY_KEY_REUSED,
                        stored,
                    )

                existing = connection.execute(
                    text(
                        self._participation_select()
                        + " WHERE actor_id = :actor_id AND card_version_id = :card_version_id FOR UPDATE"
                    ),
                    {
                        "actor_id": participation.actor_id,
                        "card_version_id": participation.card_version_id,
                    },
                ).mappings().one_or_none()
                if existing is not None:
                    return ConsensusParticipationAttempt(
                        ConsensusParticipationStatus.ALREADY_PARTICIPATED,
                        self._participation(existing),
                    )

                connection.execute(
                    text(
                        """
                        INSERT INTO collective.consensus_participation (
                            id, card_version_id, session_id, actor_id, case_version_id,
                            stance_code, reason_tag_codes, contribution_class,
                            idempotency_key, participated_at
                        ) VALUES (
                            :id, :card_version_id, :session_id, :actor_id, :case_version_id,
                            :stance_code, CAST(:reason_tag_codes AS jsonb), :contribution_class,
                            :idempotency_key, :participated_at
                        )
                        """
                    ),
                    {
                        "id": participation.id,
                        "card_version_id": participation.card_version_id,
                        "session_id": participation.session_id,
                        "actor_id": participation.actor_id,
                        "case_version_id": participation.case_version_id,
                        "stance_code": participation.stance_code,
                        "reason_tag_codes": json.dumps(list(participation.reason_tag_codes), separators=(",", ":")),
                        "contribution_class": participation.contribution_class,
                        "idempotency_key": participation.idempotency_key,
                        "participated_at": participation.participated_at,
                    },
                )
                return ConsensusParticipationAttempt(
                    ConsensusParticipationStatus.CREATED,
                    participation,
                )
        except IntegrityError:
            replay = self._get_by_idempotency(
                actor_id=participation.actor_id,
                idempotency_key=participation.idempotency_key,
            )
            if replay is not None:
                return ConsensusParticipationAttempt(
                    ConsensusParticipationStatus.IDEMPOTENT_REPLAY
                    if replay.card_version_id == participation.card_version_id
                    else ConsensusParticipationStatus.IDEMPOTENCY_KEY_REUSED,
                    replay,
                )
            existing = self.get_participation(
                actor_id=participation.actor_id,
                card_version_id=participation.card_version_id,
            )
            if existing is not None:
                return ConsensusParticipationAttempt(
                    ConsensusParticipationStatus.ALREADY_PARTICIPATED,
                    existing,
                )
            raise

    def aggregate(
        self,
        *,
        card: ConsensusCardVersion,
        contribution_class: str,
        generated_at: datetime,
    ) -> ConsensusAggregate:
        with self._engine.connect() as connection:
            stance_rows = connection.execute(
                text(
                    """
                    SELECT stance_code, count(*) AS count
                    FROM collective.consensus_participation
                    WHERE card_version_id = :card_version_id
                      AND contribution_class = :contribution_class
                    GROUP BY stance_code
                    """
                ),
                {"card_version_id": card.id, "contribution_class": contribution_class},
            ).mappings().all()
            reason_rows = connection.execute(
                text(
                    """
                    SELECT tag, count(*) AS count
                    FROM collective.consensus_participation cp
                    CROSS JOIN LATERAL jsonb_array_elements_text(cp.reason_tag_codes) tag
                    WHERE cp.card_version_id = :card_version_id
                      AND cp.contribution_class = :contribution_class
                    GROUP BY tag
                    """
                ),
                {"card_version_id": card.id, "contribution_class": contribution_class},
            ).mappings().all()

        stance_counts = {row["stance_code"]: int(row["count"]) for row in stance_rows}
        reason_counts = {row["tag"]: int(row["count"]) for row in reason_rows}
        sample_size = sum(stance_counts.values())
        divisor = sample_size if sample_size > 0 else 1
        return ConsensusAggregate.create(
            card_version_id=card.id,
            case_version_id=card.case_version_id,
            contribution_class=contribution_class,
            sample_size=sample_size,
            stance_distribution={
                code: stance_counts.get(code, 0) / divisor for code in card.stance_codes
            },
            reason_pattern_distribution={
                code: reason_counts.get(code, 0) / divisor
                for code in card.reason_tag_codes
                if reason_counts.get(code, 0) > 0
            },
            methodology_version=card.methodology_version,
            generated_at=generated_at,
            provenance_note=(
                "Post-commit EXPOSED Consensus sample. It is descriptive WE data and "
                "is not pooled into the core pre-result result or a Signal."
            ),
        )

    @staticmethod
    def _participation_select() -> str:
        return """
            SELECT id, card_version_id, session_id, actor_id, case_version_id,
                   stance_code, reason_tag_codes, contribution_class,
                   idempotency_key, participated_at
            FROM collective.consensus_participation
        """

    @staticmethod
    def _card(row) -> ConsensusCardVersion:
        return ConsensusCardVersion(
            id=row["id"],
            card_id=row["card_id"],
            version_no=row["version_no"],
            case_version_id=row["case_version_id"],
            proposition=row["proposition"],
            stance_codes=tuple(row["stance_codes"]),
            reason_tag_codes=tuple(row["reason_tag_codes"]),
            max_reason_tags=row["max_reason_tags"],
            methodology_version=row["methodology_version"],
            published_at=row["published_at"],
        )

    @staticmethod
    def _participation(row) -> ConsensusParticipation:
        return ConsensusParticipation(
            id=row["id"],
            card_version_id=row["card_version_id"],
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            case_version_id=row["case_version_id"],
            stance_code=row["stance_code"],
            reason_tag_codes=tuple(row["reason_tag_codes"]),
            contribution_class=row["contribution_class"],
            idempotency_key=row["idempotency_key"],
            participated_at=row["participated_at"],
        )

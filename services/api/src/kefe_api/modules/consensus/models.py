from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID


class ConsensusStance(StrEnum):
    AGREE = "AGREE"
    MIXED = "MIXED"
    DISAGREE = "DISAGREE"


class ConsensusContributionClass(StrEnum):
    EXPOSED = "EXPOSED"


class ConsensusParticipationStatus(StrEnum):
    CREATED = "CREATED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    ALREADY_PARTICIPATED = "ALREADY_PARTICIPATED"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"


@dataclass(frozen=True, slots=True)
class ConsensusCardVersion:
    id: UUID
    case_version_id: UUID
    proposition: str
    stance_codes: tuple[str, ...]
    reason_tag_codes: tuple[str, ...]
    max_reason_tags: int
    methodology_version: str
    published_at: datetime


@dataclass(frozen=True, slots=True)
class ConsensusParticipation:
    id: UUID
    card_version_id: UUID
    session_id: UUID
    actor_id: UUID
    case_version_id: UUID
    stance_code: str
    reason_tag_codes: tuple[str, ...]
    contribution_class: str
    idempotency_key: str
    participated_at: datetime


@dataclass(frozen=True, slots=True)
class ConsensusParticipationAttempt:
    status: ConsensusParticipationStatus
    participation: ConsensusParticipation | None = None


@dataclass(frozen=True, slots=True)
class ConsensusAggregate:
    card_version_id: UUID
    case_version_id: UUID
    contribution_class: str
    sample_size: int
    stance_distribution: Mapping[str, float]
    reason_pattern_distribution: Mapping[str, float]
    methodology_version: str
    generated_at: datetime
    provenance_note: str

    @classmethod
    def create(
        cls,
        *,
        card_version_id: UUID,
        case_version_id: UUID,
        contribution_class: str,
        sample_size: int,
        stance_distribution: Mapping[str, float],
        reason_pattern_distribution: Mapping[str, float],
        methodology_version: str,
        generated_at: datetime,
        provenance_note: str,
    ) -> ConsensusAggregate:
        return cls(
            card_version_id=card_version_id,
            case_version_id=case_version_id,
            contribution_class=contribution_class,
            sample_size=sample_size,
            stance_distribution=MappingProxyType(dict(stance_distribution)),
            reason_pattern_distribution=MappingProxyType(dict(reason_pattern_distribution)),
            methodology_version=methodology_version,
            generated_at=generated_at,
            provenance_note=provenance_note,
        )


@dataclass(frozen=True, slots=True)
class ConsensusCardView:
    card: ConsensusCardVersion
    participation: ConsensusParticipation | None
    aggregate: ConsensusAggregate | None

    @property
    def participation_state(self) -> str:
        return "PARTICIPATED" if self.participation is not None else "ELIGIBLE"

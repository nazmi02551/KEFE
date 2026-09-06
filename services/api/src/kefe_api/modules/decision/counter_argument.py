from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class RefutationType(StrEnum):
    DIRECT_EMPIRICAL_REBUTTAL = "DIRECT_EMPIRICAL_REBUTTAL"
    LOGICAL_INVALIDATION = "LOGICAL_INVALIDATION"
    VALUE_HIERARCHY_CHALLENGE = "VALUE_HIERARCHY_CHALLENGE"
    BOUNDARY_QUALIFICATION = "BOUNDARY_QUALIFICATION"


@dataclass(frozen=True, slots=True)
class ArgumentRefutationLink:
    refutation_id: UUID
    source_argument_id: UUID
    target_argument_id: UUID
    refutation_type: RefutationType
    refutation_strength: float
    rebuttal_thesis: str


class CounterArgumentMapperService:
    def __init__(self) -> None:
        self._links: dict[UUID, ArgumentRefutationLink] = {}

    def map_refutation(
        self,
        *,
        source_argument_id: UUID,
        target_argument_id: UUID,
        refutation_type: RefutationType,
        refutation_strength: float,
        rebuttal_thesis: str,
    ) -> ArgumentRefutationLink:
        if source_argument_id == target_argument_id:
            raise ValueError("An argument cannot target itself as a refutation")
        if not 0.0 <= refutation_strength <= 1.0:
            raise ValueError(f"refutation_strength must be in [0.0, 1.0], got {refutation_strength}")
        if len(rebuttal_thesis.strip()) < 10:
            raise ValueError("rebuttal_thesis must have at least 10 characters")

        link_id = uuid4()
        link = ArgumentRefutationLink(
            refutation_id=link_id,
            source_argument_id=source_argument_id,
            target_argument_id=target_argument_id,
            refutation_type=refutation_type,
            refutation_strength=round(refutation_strength, 2),
            rebuttal_thesis=rebuttal_thesis.strip(),
        )

        self._links[link_id] = link
        return link

    def get_rebuttals_for_target(self, target_argument_id: UUID) -> list[ArgumentRefutationLink]:
        return [
            link for link in self._links.values()
            if link.target_argument_id == target_argument_id
        ]

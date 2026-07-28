from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping
from uuid import UUID, uuid4


class ContentConfigLifecycle(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class ContentConfigurationSnapshot:
    id: UUID
    version_no: int
    state: ContentConfigLifecycle
    domains: frozenset[str]
    base_formats: frozenset[str]
    modifiers: frozenset[str]
    risks: frozenset[str]
    claim_states: frozenset[str]
    review_modes: frozenset[str]
    allowed_modifiers: Mapping[str, frozenset[str]]
    review_modes_by_risk: Mapping[str, frozenset[str]]
    created_at: datetime
    published_at: datetime | None = None

    @classmethod
    def create_draft(
        cls,
        *,
        version_no: int,
        domains: frozenset[str],
        base_formats: frozenset[str],
        modifiers: frozenset[str],
        risks: frozenset[str],
        claim_states: frozenset[str],
        review_modes: frozenset[str],
        allowed_modifiers: Mapping[str, frozenset[str]],
        review_modes_by_risk: Mapping[str, frozenset[str]],
    ) -> ContentConfigurationSnapshot:
        return cls(
            id=uuid4(),
            version_no=version_no,
            state=ContentConfigLifecycle.DRAFT,
            domains=domains,
            base_formats=base_formats,
            modifiers=modifiers,
            risks=risks,
            claim_states=claim_states,
            review_modes=review_modes,
            allowed_modifiers=MappingProxyType(dict(allowed_modifiers)),
            review_modes_by_risk=MappingProxyType(dict(review_modes_by_risk)),
            created_at=datetime.now(UTC),
        )

    def with_state(
        self,
        state: ContentConfigLifecycle,
        *,
        published_at: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        return replace(self, state=state, published_at=published_at)


@dataclass(frozen=True, slots=True)
class ContentConfigurationAuditEntry:
    id: UUID
    snapshot_id: UUID
    actor_ref: str
    command: str
    previous_state: ContentConfigLifecycle | None
    new_state: ContentConfigLifecycle
    occurred_at: datetime
    superseded_snapshot_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        snapshot: ContentConfigurationSnapshot,
        actor_ref: str,
        command: str,
        previous_state: ContentConfigLifecycle | None,
        new_state: ContentConfigLifecycle,
        superseded_snapshot_id: UUID | None = None,
    ) -> ContentConfigurationAuditEntry:
        return cls(
            id=uuid4(),
            snapshot_id=snapshot.id,
            actor_ref=actor_ref,
            command=command,
            previous_state=previous_state,
            new_state=new_state,
            occurred_at=datetime.now(UTC),
            superseded_snapshot_id=superseded_snapshot_id,
        )

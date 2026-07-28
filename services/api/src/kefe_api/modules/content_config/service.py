from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from types import MappingProxyType
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_config.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)
from kefe_api.modules.content_config.ports import ContentConfigurationRepository

_CODE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ContentConfigurationService:
    def __init__(self, repository: ContentConfigurationRepository) -> None:
        self._repository = repository

    def current(self) -> ContentConfigurationSnapshot:
        snapshot = self._repository.current_published()
        if snapshot is None:
            raise DomainError(
                "CONTENT_CONFIGURATION_UNAVAILABLE",
                "No published content configuration is available",
                503,
                retryable=True,
            )
        return snapshot

    def create_draft(self) -> ContentConfigurationSnapshot:
        current = self.current()
        draft = replace(
            current,
            id=UUID(int=0),
            version_no=self._repository.next_version_no(),
            state=ContentConfigLifecycle.DRAFT,
            created_at=datetime.now(UTC),
            published_at=None,
        )
        # Preserve immutable collection semantics while assigning a new stable snapshot identity.
        draft = ContentConfigurationSnapshot.create_draft(
            version_no=draft.version_no,
            domains=draft.domains,
            base_formats=draft.base_formats,
            modifiers=draft.modifiers,
            risks=draft.risks,
            claim_states=draft.claim_states,
            review_modes=draft.review_modes,
            allowed_modifiers=draft.allowed_modifiers,
            review_modes_by_risk=draft.review_modes_by_risk,
        )
        self._repository.save_draft(draft)
        return draft

    def get(self, snapshot_id: UUID) -> ContentConfigurationSnapshot:
        snapshot = self._repository.get_snapshot(snapshot_id)
        if snapshot is None:
            raise DomainError("CONTENT_CONFIGURATION_NOT_FOUND", "Configuration not found", 404)
        return snapshot

    def save_draft(
        self,
        snapshot_id: UUID,
        *,
        domains: frozenset[str],
        base_formats: frozenset[str],
        modifiers: frozenset[str],
        risks: frozenset[str],
        claim_states: frozenset[str],
        review_modes: frozenset[str],
        allowed_modifiers: dict[str, frozenset[str]],
        review_modes_by_risk: dict[str, frozenset[str]],
    ) -> ContentConfigurationSnapshot:
        current = self.get(snapshot_id)
        if current.state is not ContentConfigLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_CONFIGURATION_IMMUTABLE",
                "Only DRAFT configuration snapshots can be edited",
                409,
            )
        updated = replace(
            current,
            domains=domains,
            base_formats=base_formats,
            modifiers=modifiers,
            risks=risks,
            claim_states=claim_states,
            review_modes=review_modes,
            allowed_modifiers=MappingProxyType(dict(allowed_modifiers)),
            review_modes_by_risk=MappingProxyType(dict(review_modes_by_risk)),
        )
        self._validate(updated)
        try:
            self._repository.save_draft(updated)
        except ValueError as exc:
            raise DomainError(
                "CONTENT_CONFIGURATION_CONFLICT",
                "Configuration changed concurrently",
                409,
                detail=str(exc),
            ) from exc
        return updated

    def publish(
        self,
        snapshot_id: UUID,
        *,
        actor_ref: str,
    ) -> ContentConfigurationSnapshot:
        current = self.get(snapshot_id)
        if current.state is not ContentConfigLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_CONFIGURATION_INVALID_STATE",
                "Only DRAFT configuration snapshots can be published",
                409,
            )
        self._validate(current)
        published = current.with_state(
            ContentConfigLifecycle.PUBLISHED,
            published_at=datetime.now(UTC),
        )
        previous = self._repository.current_published()
        audit = ContentConfigurationAuditEntry.create(
            snapshot=current,
            actor_ref=actor_ref,
            command="publish",
            previous_state=ContentConfigLifecycle.DRAFT,
            new_state=ContentConfigLifecycle.PUBLISHED,
            superseded_snapshot_id=previous.id if previous else None,
        )
        try:
            result, _ = self._repository.publish_atomically(snapshot=published, audit=audit)
        except ValueError as exc:
            raise DomainError(
                "CONTENT_CONFIGURATION_CONFLICT",
                "Configuration changed concurrently",
                409,
                detail=str(exc),
            ) from exc
        return result

    def audit(self) -> tuple[ContentConfigurationAuditEntry, ...]:
        return self._repository.list_audit()

    @staticmethod
    def _validate(snapshot: ContentConfigurationSnapshot) -> None:
        collections = {
            "domains": snapshot.domains,
            "base_formats": snapshot.base_formats,
            "risks": snapshot.risks,
            "claim_states": snapshot.claim_states,
        }
        for field, values in collections.items():
            if not values:
                raise DomainError(
                    "CONTENT_CONFIGURATION_INVALID",
                    f"{field} must contain at least one code",
                    422,
                    meta={"field": field},
                )

        all_codes = (
            snapshot.domains
            | snapshot.base_formats
            | snapshot.modifiers
            | snapshot.risks
            | snapshot.claim_states
            | snapshot.review_modes
        )
        invalid_codes = sorted(code for code in all_codes if _CODE.fullmatch(code) is None)
        if invalid_codes:
            raise DomainError(
                "CONTENT_CONFIGURATION_INVALID",
                "Configuration contains non-canonical codes",
                422,
                meta={"invalid_codes": invalid_codes},
            )

        for base_format, modifiers in snapshot.allowed_modifiers.items():
            if base_format not in snapshot.base_formats:
                raise DomainError(
                    "CONTENT_CONFIGURATION_INVALID",
                    "Modifier compatibility references unknown base format",
                    422,
                    meta={"base_format": base_format},
                )
            unknown = sorted(modifiers - snapshot.modifiers)
            if unknown:
                raise DomainError(
                    "CONTENT_CONFIGURATION_INVALID",
                    "Modifier compatibility references unknown modifiers",
                    422,
                    meta={"base_format": base_format, "unknown_modifiers": unknown},
                )

        for risk, modes in snapshot.review_modes_by_risk.items():
            if risk not in snapshot.risks:
                raise DomainError(
                    "CONTENT_CONFIGURATION_INVALID",
                    "Review policy references unknown risk",
                    422,
                    meta={"risk": risk},
                )
            unknown = sorted(modes - snapshot.review_modes)
            if unknown:
                raise DomainError(
                    "CONTENT_CONFIGURATION_INVALID",
                    "Review policy references unknown review modes",
                    422,
                    meta={"risk": risk, "unknown_review_modes": unknown},
                )

from __future__ import annotations

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    PublicationValidationFailure,
)
from kefe_api.modules.content_authoring.registry import InMemoryContentAuthoringRegistry
from kefe_api.modules.content_config.ports import ContentConfigurationRepository


def _single_choice(schema: dict[str, object]) -> bool:
    options = schema.get("options")
    return isinstance(options, list) and len(options) >= 2


def _confidence(schema: dict[str, object]) -> bool:
    return schema.get("min") == 1 and schema.get("max") == 10


class PublishedContentAuthoringRegistry:
    """Adapts the active published configuration snapshot to authoring validation."""

    def __init__(self, repository: ContentConfigurationRepository) -> None:
        self._repository = repository

    def validate(
        self,
        version: AuthoringCaseVersion,
    ) -> tuple[PublicationValidationFailure, ...]:
        snapshot = self._repository.current_published()
        if snapshot is None:
            raise DomainError(
                "CONTENT_CONFIGURATION_UNAVAILABLE",
                "No published content configuration is available",
                503,
                retryable=True,
            )

        registry = InMemoryContentAuthoringRegistry(
            base_formats=snapshot.base_formats,
            domains=snapshot.domains,
            risks=snapshot.risks,
            claim_states=snapshot.claim_states,
            response_schema_validators={
                "SINGLE_CHOICE": _single_choice,
                "CONFIDENCE": _confidence,
            },
            allowed_modifiers=dict(snapshot.allowed_modifiers),
        )
        failures = list(registry.validate(version))
        required_modes = snapshot.review_modes_by_risk.get(version.content_risk, frozenset())
        missing = sorted(required_modes - set(version.completed_review_modes))
        if missing:
            failures.append(
                PublicationValidationFailure(
                    code="CONTENT_POLICY_REVIEW_REQUIRED",
                    detail="Missing configuration-required review modes: " + ", ".join(missing),
                    path="completed_review_modes",
                )
            )
        return tuple(failures)

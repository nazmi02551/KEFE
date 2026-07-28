from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    PublicationValidationFailure,
)

SchemaValidator = Callable[[dict[str, Any]], bool]


@dataclass(slots=True)
class InMemoryContentAuthoringRegistry:
    """Configuration-backed registry adapter for authoring validation tests and bootstrap."""

    base_formats: frozenset[str]
    domains: frozenset[str]
    risks: frozenset[str]
    claim_states: frozenset[str]
    response_schema_validators: dict[str, SchemaValidator]
    allowed_modifiers: dict[str, frozenset[str]] = field(default_factory=dict)

    def validate(
        self,
        version: AuthoringCaseVersion,
    ) -> tuple[PublicationValidationFailure, ...]:
        failures: list[PublicationValidationFailure] = []

        if not version.title.strip():
            failures.append(
                self._failure("CONTENT_TITLE_REQUIRED", "Title is required", "title")
            )
        if not version.summary.strip():
            failures.append(
                self._failure(
                    "CONTENT_SUMMARY_REQUIRED",
                    "Summary is required",
                    "summary",
                )
            )
        if version.base_format_code not in self.base_formats:
            failures.append(
                self._failure(
                    "CONTENT_FORMAT_UNKNOWN",
                    f"Unknown base format: {version.base_format_code}",
                    "base_format_code",
                )
            )
        if version.primary_domain_code not in self.domains:
            failures.append(
                self._failure(
                    "CONTENT_DOMAIN_UNKNOWN",
                    f"Unknown domain: {version.primary_domain_code}",
                    "primary_domain_code",
                )
            )
        if version.content_risk not in self.risks:
            failures.append(
                self._failure(
                    "CONTENT_RISK_UNKNOWN",
                    f"Unknown content risk: {version.content_risk}",
                    "content_risk",
                )
            )

        if not version.issues:
            failures.append(
                self._failure("CONTENT_ISSUE_REQUIRED", "At least one Issue is required", "issues")
            )
        if not version.active_questions:
            failures.append(
                self._failure(
                    "CONTENT_ACTIVE_QUESTION_REQUIRED",
                    "At least one active Question is required",
                    "issues.questions",
                )
            )

        for question in version.active_questions:
            validator = self.response_schema_validators.get(question.response_type)
            if validator is None:
                failures.append(
                    self._failure(
                        "CONTENT_RESPONSE_TYPE_UNKNOWN",
                        f"Unknown response type: {question.response_type}",
                        f"question:{question.id}",
                    )
                )
            elif not validator(question.response_schema):
                failures.append(
                    self._failure(
                        "CONTENT_RESPONSE_SCHEMA_INVALID",
                        f"Invalid schema for response type: {question.response_type}",
                        f"question:{question.id}",
                    )
                )

        allowed_for_format = self.allowed_modifiers.get(version.base_format_code, frozenset())
        invalid_modifiers = sorted(set(version.modifiers) - allowed_for_format)
        if invalid_modifiers:
            failures.append(
                self._failure(
                    "CONTENT_MODIFIER_INCOMPATIBLE",
                    "Incompatible modifiers: " + ", ".join(invalid_modifiers),
                    "modifiers",
                )
            )

        if (version.is_fact_bearing or version.is_real_event) and not version.sources:
            failures.append(
                self._failure(
                    "CONTENT_SOURCE_REQUIRED",
                    "Fact-bearing or real-event content requires at least one source",
                    "sources",
                )
            )

        for source in version.sources:
            if source.claim_status is not None and source.claim_status not in self.claim_states:
                failures.append(
                    self._failure(
                        "CONTENT_CLAIM_STATE_UNKNOWN",
                        f"Unknown claim state: {source.claim_status}",
                        f"source:{source.id}",
                    )
                )
            if version.is_fact_bearing and source.claim_status is None:
                failures.append(
                    self._failure(
                        "CONTENT_CLAIM_STATE_REQUIRED",
                        "Fact-bearing source references require a claim state",
                        f"source:{source.id}",
                    )
                )

        missing_reviews = sorted(
            set(version.required_review_modes) - set(version.completed_review_modes)
        )
        if missing_reviews:
            failures.append(
                self._failure(
                    "CONTENT_REVIEW_REQUIRED",
                    "Missing required review modes: " + ", ".join(missing_reviews),
                    "completed_review_modes",
                )
            )

        return tuple(failures)

    @staticmethod
    def _failure(code: str, detail: str, path: str) -> PublicationValidationFailure:
        return PublicationValidationFailure(code=code, detail=detail, path=path)


def default_authoring_registry() -> InMemoryContentAuthoringRegistry:
    return InMemoryContentAuthoringRegistry(
        base_formats=frozenset({"TODAY", "DILEMMA", "LAB", "VS", "CALL", "DECIDE", "RETRO"}),
        domains=frozenset(
            {
                "CIVIC_POLITICS",
                "LAW_JUSTICE",
                "SPORTS",
                "TECHNOLOGY_AI",
                "WORK_BUSINESS",
                "EDUCATION",
                "FAMILY_PARENTING",
                "RELATIONSHIPS",
                "ECONOMY_MONEY",
                "HEALTH_BIOETHICS",
                "SCIENCE_FUTURE",
                "PLANET_ANIMALS",
                "CITY_PUBLIC_LIFE",
                "CULTURE_MEDIA",
                "WORLD_GEOPOLITICS",
                "DAILY_LIFE",
            }
        ),
        risks=frozenset({"L0", "L1", "L2", "L3"}),
        claim_states=frozenset({"VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"}),
        response_schema_validators={
            "SINGLE_CHOICE": lambda schema: isinstance(schema.get("options"), list)
            and len(schema["options"]) >= 2,
            "CONFIDENCE": lambda schema: schema.get("min") == 1 and schema.get("max") == 10,
        },
        allowed_modifiers={
            "TODAY": frozenset(
                {
                    "PROGRESSIVE_DISCLOSURE",
                    "SOURCE_REVEAL",
                    "EVOLVE",
                    "SENSITIVE_MODE",
                    "CIVIC_INTEGRITY",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "DILEMMA": frozenset(
                {
                    "BLIND_FIRST",
                    "PROGRESSIVE_DISCLOSURE",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "LAB": frozenset(
                {
                    "BLIND_FIRST",
                    "IDENTITY_REVEAL",
                    "SOURCE_REVEAL",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "VS": frozenset({"BLIND_FIRST", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
            "CALL": frozenset(
                {
                    "BLIND_FIRST",
                    "OFFICIAL_DECISION_COMPARE",
                    "EXPERT_COMPARE",
                    "EVOLVE",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "DECIDE": frozenset({"EVOLVE", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
            "RETRO": frozenset({"OUTCOME_REVEAL", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
        },
    )

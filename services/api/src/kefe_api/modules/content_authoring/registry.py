from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    MarketScope,
    PublicationValidationFailure,
)

SchemaValidator = Callable[[dict[str, Any]], bool]

_SOURCE_KINDS = frozenset({"OFFICIAL", "NEWS", "RESEARCH", "EDITORIAL", "OTHER"})
_DISCLOSURE_LEVELS = frozenset({"ESSENTIAL", "DETAIL"})
_LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
_COUNTRY_CODE = re.compile(r"^[A-Z]{2}$")


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

        self._validate_identity_fields(version, failures)
        self._validate_questions(version, failures)
        self._validate_modifiers(version, failures)
        self._validate_sources_and_context(version, failures)
        self._validate_globalization(version, failures)
        self._validate_reviews(version, failures)
        return tuple(failures)

    def _validate_identity_fields(
        self,
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
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

    def _validate_questions(
        self,
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
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

    def _validate_modifiers(
        self,
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
        allowed = self.allowed_modifiers.get(version.base_format_code, frozenset())
        invalid = sorted(set(version.modifiers) - allowed)
        if invalid:
            failures.append(
                self._failure(
                    "CONTENT_MODIFIER_INCOMPATIBLE",
                    "Incompatible modifiers: " + ", ".join(invalid),
                    "modifiers",
                )
            )

    def _validate_sources_and_context(
        self,
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
        if (version.is_fact_bearing or version.is_real_event) and not version.sources:
            failures.append(
                self._failure(
                    "CONTENT_SOURCE_REQUIRED",
                    "Fact-bearing or real-event content requires at least one source",
                    "sources",
                )
            )

        source_ids = {source.id for source in version.sources}
        for source in version.sources:
            if source.source_kind not in _SOURCE_KINDS:
                failures.append(
                    self._failure(
                        "CONTENT_SOURCE_KIND_UNKNOWN",
                        f"Unknown source kind: {source.source_kind}",
                        f"source:{source.id}",
                    )
                )
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

        for block in version.context_blocks:
            if block.disclosure_level not in _DISCLOSURE_LEVELS:
                failures.append(
                    self._failure(
                        "CONTENT_DISCLOSURE_LEVEL_UNKNOWN",
                        f"Unknown disclosure level: {block.disclosure_level}",
                        f"context:{block.id}",
                    )
                )
            if block.claim_status not in self.claim_states:
                failures.append(
                    self._failure(
                        "CONTENT_CLAIM_STATE_UNKNOWN",
                        f"Unknown claim state: {block.claim_status}",
                        f"context:{block.id}",
                    )
                )
            unknown_sources = sorted(
                (source_id for source_id in block.source_ids if source_id not in source_ids),
                key=str,
            )
            if unknown_sources:
                failures.append(
                    self._failure(
                        "CONTENT_CONTEXT_SOURCE_UNKNOWN",
                        "Context references unknown source IDs: "
                        + ", ".join(str(source_id) for source_id in unknown_sources),
                        f"context:{block.id}",
                    )
                )

    def _validate_globalization(
        self,
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
        if not _LANGUAGE_TAG.fullmatch(version.content_locale):
            failures.append(
                self._failure(
                    "CONTENT_LOCALE_INVALID",
                    "content_locale must be a normalized language tag such as tr-TR or en-US",
                    "content_locale",
                )
            )

        normalized_countries = tuple(dict.fromkeys(version.country_codes))
        invalid_countries = [
            code for code in normalized_countries if not _COUNTRY_CODE.fullmatch(code)
        ]
        if invalid_countries:
            failures.append(
                self._failure(
                    "CONTENT_COUNTRY_CODE_INVALID",
                    "Invalid ISO-3166 alpha-2 country codes: " + ", ".join(invalid_countries),
                    "country_codes",
                )
            )
        if len(normalized_countries) > 32:
            failures.append(
                self._failure(
                    "CONTENT_COUNTRY_SCOPE_TOO_LARGE",
                    "A CaseVersion may target at most 32 explicit countries",
                    "country_codes",
                )
            )
        if version.market_scope is MarketScope.GLOBAL and normalized_countries:
            failures.append(
                self._failure(
                    "CONTENT_GLOBAL_COUNTRY_SET_FORBIDDEN",
                    "GLOBAL content cannot also provide country_codes",
                    "country_codes",
                )
            )
        if version.market_scope is MarketScope.COUNTRY_SET and not normalized_countries:
            failures.append(
                self._failure(
                    "CONTENT_COUNTRY_SET_REQUIRED",
                    "COUNTRY_SET content requires at least one country code",
                    "country_codes",
                )
            )

        active_questions = {question.stable_code: question for question in version.active_questions}
        seen_locales: set[str] = set()
        for localization in version.localizations:
            path = f"localizations:{localization.locale}"
            if not _LANGUAGE_TAG.fullmatch(localization.locale):
                failures.append(
                    self._failure(
                        "CONTENT_LOCALIZATION_LOCALE_INVALID",
                        f"Invalid localization locale: {localization.locale}",
                        path,
                    )
                )
            if localization.locale in seen_locales:
                failures.append(
                    self._failure(
                        "CONTENT_LOCALIZATION_DUPLICATE",
                        f"Duplicate localization locale: {localization.locale}",
                        path,
                    )
                )
            seen_locales.add(localization.locale)
            if not localization.title.strip() or not localization.summary.strip():
                failures.append(
                    self._failure(
                        "CONTENT_LOCALIZATION_COPY_REQUIRED",
                        "Localized title and summary are required",
                        path,
                    )
                )
            unknown_questions = sorted(
                set(localization.question_prompts) | set(localization.option_labels)
                - set(active_questions)
            )
            if unknown_questions:
                failures.append(
                    self._failure(
                        "CONTENT_LOCALIZATION_QUESTION_UNKNOWN",
                        "Localization references unknown stable question codes: "
                        + ", ".join(unknown_questions),
                        path,
                    )
                )
            for stable_code, labels in localization.option_labels.items():
                question = active_questions.get(stable_code)
                if question is None:
                    continue
                canonical_options = {
                    str(value) for value in question.response_schema.get("options", [])
                }
                unknown_values = sorted(set(labels) - canonical_options)
                if unknown_values:
                    failures.append(
                        self._failure(
                            "CONTENT_LOCALIZATION_OPTION_UNKNOWN",
                            "Localized labels reference unknown canonical option values: "
                            + ", ".join(unknown_values),
                            f"{path}.option_labels.{stable_code}",
                        )
                    )

    @staticmethod
    def _validate_reviews(
        version: AuthoringCaseVersion,
        failures: list[PublicationValidationFailure],
    ) -> None:
        missing_reviews = sorted(
            set(version.required_review_modes) - set(version.completed_review_modes)
        )
        if missing_reviews:
            failures.append(
                PublicationValidationFailure(
                    code="CONTENT_REVIEW_REQUIRED",
                    detail="Missing required review modes: " + ", ".join(missing_reviews),
                    path="completed_review_modes",
                )
            )

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

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import CaseLocalization, CaseVersion, Question
from kefe_api.modules.decision.ports import DecisionRepository

_LOCALE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
_COUNTRY = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True, slots=True)
class LocalizedQuestionView:
    question: Question
    prompt: str
    option_labels: dict[str, str]


@dataclass(frozen=True, slots=True)
class LocalizedCaseView:
    case: CaseVersion
    requested_locale: str
    display_locale: str
    localized: bool
    title: str
    summary: str
    cultural_context_note: str | None
    legal_context_note: str | None
    questions: tuple[LocalizedQuestionView, ...]


class GlobalDiscoveryService:
    def __init__(self, repository: DecisionRepository) -> None:
        self._repository = repository

    def list_cases(
        self,
        *,
        locale: str,
        country: str | None,
        limit: int,
    ) -> tuple[LocalizedCaseView, ...]:
        normalized_locale = self.normalize_locale(locale)
        normalized_country = self.normalize_country(country)
        bounded_limit = min(max(limit, 1), 50)
        candidates = self._repository.list_current_cases(limit=50)
        visible = (
            case
            for case in candidates
            if self._is_market_visible(case, normalized_country)
        )
        return tuple(
            self._localize(case, normalized_locale)
            for case in visible
        )[:bounded_limit]

    def get_case(
        self,
        case_id: UUID,
        *,
        locale: str,
        country: str | None,
    ) -> LocalizedCaseView:
        normalized_locale = self.normalize_locale(locale)
        normalized_country = self.normalize_country(country)
        case = self._repository.get_current_case_version(case_id)
        if case is None or not self._is_market_visible(case, normalized_country):
            raise DomainError("CASE_NOT_FOUND", "Case not found for requested market", 404)
        return self._localize(case, normalized_locale)

    @staticmethod
    def normalize_locale(value: str) -> str:
        raw = value.strip().replace("_", "-")
        parts = raw.split("-")
        normalized = parts[0].lower()
        if len(parts) == 2:
            normalized += "-" + parts[1].upper()
        if len(parts) > 2 or not _LOCALE.fullmatch(normalized):
            raise DomainError("DISCOVERY_LOCALE_INVALID", "Invalid locale", 422)
        return normalized

    @staticmethod
    def normalize_country(value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().upper()
        if not _COUNTRY.fullmatch(normalized):
            raise DomainError("DISCOVERY_COUNTRY_INVALID", "Invalid country code", 422)
        return normalized

    @staticmethod
    def _is_market_visible(case: CaseVersion, country: str | None) -> bool:
        if case.market_scope == "GLOBAL":
            return True
        return country is not None and country in case.country_codes

    def _localize(self, case: CaseVersion, requested_locale: str) -> LocalizedCaseView:
        localization = self._select_localization(case, requested_locale)
        if localization is None:
            return LocalizedCaseView(
                case=case,
                requested_locale=requested_locale,
                display_locale=case.content_locale,
                localized=False,
                title=case.title,
                summary=case.summary,
                cultural_context_note=case.cultural_context_note,
                legal_context_note=case.legal_context_note,
                questions=tuple(
                    LocalizedQuestionView(
                        question=question,
                        prompt=question.prompt,
                        option_labels={option: option for option in question.options},
                    )
                    for question in case.questions
                ),
            )

        return LocalizedCaseView(
            case=case,
            requested_locale=requested_locale,
            display_locale=localization.locale,
            localized=True,
            title=localization.title,
            summary=localization.summary,
            cultural_context_note=(
                localization.cultural_context_note or case.cultural_context_note
            ),
            legal_context_note=(localization.legal_context_note or case.legal_context_note),
            questions=tuple(
                self._localize_question(question, localization)
                for question in case.questions
            ),
        )

    @staticmethod
    def _select_localization(
        case: CaseVersion,
        requested_locale: str,
    ) -> CaseLocalization | None:
        exact = case.localizations.get(requested_locale)
        if exact is not None:
            return exact
        language = requested_locale.split("-", 1)[0]
        matches = sorted(
            (
                item
                for locale, item in case.localizations.items()
                if locale.split("-", 1)[0] == language
            ),
            key=lambda item: item.locale,
        )
        return matches[0] if matches else None

    @staticmethod
    def _localize_question(
        question: Question,
        localization: CaseLocalization,
    ) -> LocalizedQuestionView:
        prompt = localization.question_prompts.get(question.stable_code, question.prompt)
        labels = localization.option_labels.get(question.stable_code, {})
        return LocalizedQuestionView(
            question=question,
            prompt=prompt,
            option_labels={option: labels.get(option, option) for option in question.options},
        )

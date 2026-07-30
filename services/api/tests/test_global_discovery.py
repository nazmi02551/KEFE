from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import CaseLocalization, CaseVersion, Question
from kefe_api.modules.global_discovery.service import GlobalDiscoveryService


def _case(*, market_scope: str = "GLOBAL", country_codes: tuple[str, ...] = ()) -> CaseVersion:
    question = Question(
        id=uuid4(),
        stable_code="PRIMARY",
        prompt="Kime öncelik verilmeli?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["QUEUE", "NEED"]},
    )
    return CaseVersion(
        id=uuid4(),
        case_id=uuid4(),
        title="Sırada acil ihtiyaç",
        summary="Sıra hakkı ile açık aciliyeti tart.",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=1,
        questions=(question,),
        content_locale="tr-TR",
        market_scope=market_scope,
        country_codes=country_codes,
        localizations={
            "en-US": CaseLocalization(
                locale="en-US",
                title="Urgent need in a queue",
                summary="Weigh queue order against an obvious urgent need.",
                question_prompts={"PRIMARY": "Who should get priority?"},
                option_labels={
                    "PRIMARY": {
                        "QUEUE": "Person next in line",
                        "NEED": "Person with urgent need",
                    }
                },
                cultural_context_note="Queue norms differ by context.",
            )
        },
    )


def test_global_discovery_localizes_without_changing_canonical_option_values() -> None:
    global_case = _case()
    repository = InMemoryDecisionRepository(cases=[global_case], reveals=[])
    service = GlobalDiscoveryService(repository)

    view = service.get_case(global_case.case_id, locale="en-us", country="de")

    assert view.display_locale == "en-US"
    assert view.localized is True
    assert view.title == "Urgent need in a queue"
    assert view.questions[0].prompt == "Who should get priority?"
    assert view.questions[0].option_labels == {
        "QUEUE": "Person next in line",
        "NEED": "Person with urgent need",
    }
    assert view.questions[0].question.options == ("QUEUE", "NEED")


def test_country_scoped_case_requires_matching_country_but_global_remains_visible() -> None:
    global_case = _case()
    tr_case = _case(market_scope="COUNTRY_SET", country_codes=("TR",))
    repository = InMemoryDecisionRepository(cases=[global_case, tr_case], reveals=[])
    service = GlobalDiscoveryService(repository)

    without_country = service.list_cases(locale="tr-TR", country=None, limit=20)
    in_turkiye = service.list_cases(locale="tr-TR", country="tr", limit=20)
    in_germany = service.list_cases(locale="tr-TR", country="DE", limit=20)

    assert {item.case.case_id for item in without_country} == {global_case.case_id}
    assert {item.case.case_id for item in in_turkiye} == {
        global_case.case_id,
        tr_case.case_id,
    }
    assert {item.case.case_id for item in in_germany} == {global_case.case_id}


def test_missing_translation_falls_back_transparently_to_source_locale() -> None:
    case = _case()
    repository = InMemoryDecisionRepository(cases=[case], reveals=[])
    service = GlobalDiscoveryService(repository)

    view = service.get_case(case.case_id, locale="de-DE", country=None)

    assert view.localized is False
    assert view.requested_locale == "de-DE"
    assert view.display_locale == "tr-TR"
    assert view.title == case.title


@pytest.mark.parametrize(
    ("locale", "country", "expected"),
    [
        ("english", None, "DISCOVERY_LOCALE_INVALID"),
        ("tr-TR", "TUR", "DISCOVERY_COUNTRY_INVALID"),
    ],
)
def test_invalid_locale_or_country_fails_closed(
    locale: str,
    country: str | None,
    expected: str,
) -> None:
    repository = InMemoryDecisionRepository(cases=[_case()], reveals=[])
    service = GlobalDiscoveryService(repository)

    with pytest.raises(DomainError) as error:
        service.list_cases(locale=locale, country=country, limit=20)

    assert error.value.code == expected

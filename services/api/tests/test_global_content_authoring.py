from uuid import uuid4

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseLocalization,
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    ContentLifecycle,
    MarketScope,
)
from kefe_api.modules.content_authoring.registry import default_authoring_registry


def _version(**overrides) -> AuthoringCaseVersion:
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY",
        prompt="Kime öncelik verilmeli?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["QUEUE", "NEED"]},
    )
    values = {
        "id": uuid4(),
        "case_id": uuid4(),
        "version_no": 1,
        "state": ContentLifecycle.DRAFT,
        "title": "Sırada acil ihtiyaç",
        "summary": "Sıra hakkı ile açık aciliyeti tart.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "DAILY_LIFE",
        "content_risk": "L0",
        "issues": (
            AuthoringIssue(
                id=uuid4(),
                code="PRIMARY_ISSUE",
                title="Öncelik",
                questions=(question,),
            ),
        ),
        "content_locale": "tr-TR",
        "market_scope": MarketScope.GLOBAL,
        "localizations": (
            AuthoringCaseLocalization(
                locale="en-US",
                title="Urgent need in a queue",
                summary="Weigh queue order against an urgent need.",
                question_prompts={"PRIMARY": "Who should get priority?"},
                option_labels={
                    "PRIMARY": {
                        "QUEUE": "Person next in line",
                        "NEED": "Person with urgent need",
                    }
                },
            ),
        ),
    }
    values.update(overrides)
    return AuthoringCaseVersion(**values)


def test_valid_global_localization_preserves_canonical_response_values() -> None:
    failures = default_authoring_registry().validate(_version())
    assert failures == ()


def test_country_set_requires_bounded_iso_country_codes() -> None:
    failures = default_authoring_registry().validate(
        _version(market_scope=MarketScope.COUNTRY_SET, country_codes=())
    )
    assert "CONTENT_COUNTRY_SET_REQUIRED" in {failure.code for failure in failures}

    failures = default_authoring_registry().validate(
        _version(market_scope=MarketScope.COUNTRY_SET, country_codes=("TUR",))
    )
    assert "CONTENT_COUNTRY_CODE_INVALID" in {failure.code for failure in failures}


def test_localized_option_labels_cannot_invent_response_values() -> None:
    localization = AuthoringCaseLocalization(
        locale="en-US",
        title="Urgent need in a queue",
        summary="Weigh queue order against an urgent need.",
        option_labels={"PRIMARY": {"INVENTED": "Invented"}},
    )
    failures = default_authoring_registry().validate(
        _version(localizations=(localization,))
    )
    assert "CONTENT_LOCALIZATION_OPTION_UNKNOWN" in {
        failure.code for failure in failures
    }

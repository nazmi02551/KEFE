from dataclasses import replace
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    CaseIdentity,
    ContentLifecycle,
)
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService


def _question() -> AuthoringQuestion:
    return AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Hangisini seçerdin?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )


def _issue() -> AuthoringIssue:
    return AuthoringIssue(
        id=uuid4(),
        code="PRIMARY_ISSUE",
        title="Ana karar problemi",
        questions=(_question(),),
    )


def _case_version(
    case_id,
    *,
    title: str = "İki makul seçenek arasında nasıl karar verirsin?",
    fact_bearing: bool = False,
    sources: tuple[AuthoringSourceReference, ...] = (),
    required_reviews: tuple[str, ...] = (),
    completed_reviews: tuple[str, ...] = (),
) -> AuthoringCaseVersion:
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title=title,
        summary="Düşük riskli evergreen karar senaryosu.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(_issue(),),
        modifiers=("CONFIDENCE_CAPTURE",),
        is_fact_bearing=fact_bearing,
        sources=sources,
        required_review_modes=required_reviews,
        completed_review_modes=completed_reviews,
    )


def _service():
    repository = InMemoryContentAuthoringRepository()
    service = ContentAuthoringService(repository, default_authoring_registry())
    return service, repository


def _create_ready_case(service: ContentAuthoringService):
    identity = CaseIdentity(id=uuid4(), slug=f"case-{uuid4().hex[:8]}")
    version = _case_version(identity.id)
    service.create_case(identity=identity, initial_version=version, actor_ref="editor:1")
    service.submit_for_review(version.id, actor_ref="editor:1")
    approved = service.approve(version.id, actor_ref="reviewer:1")
    return identity, approved


def test_authoring_lifecycle_publishes_only_after_approval() -> None:
    service, repository = _service()
    identity, approved = _create_ready_case(service)

    published = service.publish(approved.id, actor_ref="publisher:1")

    assert published.state is ContentLifecycle.PUBLISHED
    assert published.published_at is not None
    audit = repository.list_audit(identity.id)
    assert [entry.command for entry in audit] == [
        "create_case",
        "submit_for_review",
        "approve",
        "publish",
    ]


def test_publication_rejects_incomplete_aggregate_with_machine_failures() -> None:
    service, _ = _service()
    identity = CaseIdentity(id=uuid4(), slug="invalid-case")
    invalid = replace(_case_version(identity.id), issues=())
    service.create_case(identity=identity, initial_version=invalid, actor_ref="editor:1")
    service.submit_for_review(invalid.id, actor_ref="editor:1")
    service.approve(invalid.id, actor_ref="reviewer:1")

    with pytest.raises(DomainError) as raised:
        service.publish(invalid.id, actor_ref="publisher:1")

    assert raised.value.code == "CONTENT_PUBLICATION_INVALID"
    failure_codes = {item["code"] for item in raised.value.meta["failures"]}
    assert "CONTENT_ISSUE_REQUIRED" in failure_codes
    assert "CONTENT_ACTIVE_QUESTION_REQUIRED" in failure_codes


def test_fact_bearing_content_requires_source_claim_state() -> None:
    service, _ = _service()
    identity = CaseIdentity(id=uuid4(), slug="fact-case")
    source = AuthoringSourceReference(
        id=uuid4(),
        source_kind="OFFICIAL",
        locator="https://example.test/source",
        title="Example source",
        claim_status=None,
        verified=True,
    )
    version = _case_version(identity.id, fact_bearing=True, sources=(source,))
    service.create_case(identity=identity, initial_version=version, actor_ref="editor:1")
    service.submit_for_review(version.id, actor_ref="editor:1")
    service.approve(version.id, actor_ref="reviewer:1")

    with pytest.raises(DomainError) as raised:
        service.publish(version.id, actor_ref="publisher:1")

    assert raised.value.code == "CONTENT_PUBLICATION_INVALID"
    assert {item["code"] for item in raised.value.meta["failures"]} == {
        "CONTENT_CLAIM_STATE_REQUIRED"
    }


def test_required_review_modes_block_publication_until_completed() -> None:
    service, _ = _service()
    identity = CaseIdentity(id=uuid4(), slug="reviewed-case")
    version = _case_version(
        identity.id,
        required_reviews=("CIVIC_INTEGRITY",),
        completed_reviews=(),
    )
    service.create_case(identity=identity, initial_version=version, actor_ref="editor:1")
    service.submit_for_review(version.id, actor_ref="editor:1")
    service.approve(version.id, actor_ref="reviewer:1")

    with pytest.raises(DomainError) as raised:
        service.publish(version.id, actor_ref="publisher:1")

    assert raised.value.code == "CONTENT_PUBLICATION_INVALID"
    assert raised.value.meta["failures"][0]["code"] == "CONTENT_REVIEW_REQUIRED"


def test_published_version_is_immutable_and_revision_supersedes_atomically() -> None:
    service, repository = _service()
    identity, approved = _create_ready_case(service)
    first = service.publish(approved.id, actor_ref="publisher:1")

    with pytest.raises(DomainError) as raised:
        service.save_draft(replace(first, title="Mutated published title"))
    assert raised.value.code == "CONTENT_PUBLISHED_IMMUTABLE"

    revision = service.create_revision(source_version_id=first.id, actor_ref="editor:2")
    revised = service.save_draft(replace(revision, title="Corrected title"))
    service.submit_for_review(revised.id, actor_ref="editor:2")
    service.approve(revised.id, actor_ref="reviewer:2")
    second = service.publish(revised.id, actor_ref="publisher:2")

    versions = repository.list_versions(identity.id)
    assert second.version_no == 2
    assert [version.state for version in versions] == [
        ContentLifecycle.SUPERSEDED,
        ContentLifecycle.PUBLISHED,
    ]
    assert repository.get_version(first.id).title == first.title
    assert repository.get_version(second.id).title == "Corrected title"
    assert any(
        entry.command == "supersede_on_publish"
        for entry in repository.list_audit(identity.id)
    )


def test_reject_requires_rationale_and_returns_version_to_draft() -> None:
    service, _ = _service()
    identity = CaseIdentity(id=uuid4(), slug="rejection-case")
    version = _case_version(identity.id)
    service.create_case(identity=identity, initial_version=version, actor_ref="editor:1")
    service.submit_for_review(version.id, actor_ref="editor:1")

    with pytest.raises(DomainError) as raised:
        service.reject(version.id, actor_ref="reviewer:1", rationale="  ")
    assert raised.value.code == "CONTENT_REJECTION_RATIONALE_REQUIRED"

    rejected = service.reject(
        version.id,
        actor_ref="reviewer:1",
        rationale="Question wording needs revision",
    )
    assert rejected.state is ContentLifecycle.DRAFT


def test_no_public_authoring_http_route_is_registered() -> None:
    from kefe_api.main import create_app

    paths = {route.path for route in create_app().routes}
    assert not any("authoring" in path or "/admin" in path for path in paths)

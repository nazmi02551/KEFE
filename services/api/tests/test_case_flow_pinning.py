from dataclasses import replace
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.main import create_app
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    CaseIdentity,
    ContentLifecycle,
)
from kefe_api.modules.content_configuration.bootstrap import DEFAULT_CONFIG_ID


def _draft(case_id) -> AuthoringCaseVersion:
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Which option?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )
    issue = AuthoringIssue(
        id=uuid4(),
        code="PRIMARY_ISSUE",
        title="Primary issue",
        questions=(question,),
    )
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="Flow pinned Case",
        summary="Case publication must freeze the resolved Flow.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        modifiers=("CONFIDENCE_CAPTURE",),
        flow_template_code="STANDARD_COMMIT_REVEAL",
        flow_template_version_no=1,
    )


def _publish(service, draft: AuthoringCaseVersion) -> AuthoringCaseVersion:
    identity = CaseIdentity(id=draft.case_id, slug=f"flow-pin-{uuid4().hex[:10]}")
    service.create_case(identity=identity, initial_version=draft, actor_ref="editor:test")
    service.submit_for_review(draft.id, actor_ref="editor:test")
    service.approve(draft.id, actor_ref="reviewer:test")
    return service.publish(draft.id, actor_ref="publisher:test")


def test_publication_pins_effective_configuration_and_resolved_flow() -> None:
    app = create_app()
    service = app.state.content_authoring_service
    repository = app.state.content_authoring_repository
    draft = _draft(uuid4())

    published = _publish(service, draft)

    assert published.content_configuration_id == DEFAULT_CONFIG_ID
    assert published.content_configuration_version_no == 1
    assert published.resolved_flow is not None
    assert published.resolved_flow.template_code == "STANDARD_COMMIT_REVEAL"
    assert published.resolved_flow.template_version_no == 1
    assert published.resolved_flow.entry_step_code == "CONTEXT"
    assert [step.code for step in published.resolved_flow.steps] == [
        "CONTEXT",
        "DECISION",
        "RESULT",
    ]

    stored = repository.get_version(published.id)
    assert stored is not None
    assert stored.content_configuration_id == DEFAULT_CONFIG_ID
    assert stored.resolved_flow == published.resolved_flow


def test_revision_keeps_flow_selection_but_clears_publication_pin() -> None:
    app = create_app()
    service = app.state.content_authoring_service
    published = _publish(service, _draft(uuid4()))

    revision = service.create_revision(
        source_version_id=published.id,
        actor_ref="editor:test",
    )

    assert revision.state is ContentLifecycle.DRAFT
    assert revision.flow_template_code == published.flow_template_code
    assert revision.flow_template_version_no == published.flow_template_version_no
    assert revision.content_configuration_id is None
    assert revision.content_configuration_version_no is None
    assert revision.resolved_flow is None


def test_publication_rejects_flow_not_available_in_published_configuration() -> None:
    app = create_app()
    service = app.state.content_authoring_service
    draft = replace(
        _draft(uuid4()),
        flow_template_code="CASE_SPECIFIC_HARDCODED_FLOW",
    )
    identity = CaseIdentity(id=draft.case_id, slug=f"invalid-flow-{uuid4().hex[:10]}")
    service.create_case(identity=identity, initial_version=draft, actor_ref="editor:test")
    service.submit_for_review(draft.id, actor_ref="editor:test")
    service.approve(draft.id, actor_ref="reviewer:test")

    with pytest.raises(DomainError) as raised:
        service.publish(draft.id, actor_ref="publisher:test")

    assert raised.value.code == "CONTENT_PUBLICATION_INVALID"
    assert raised.value.meta["failures"][0]["code"] == "CONTENT_CONFIG_FLOW_UNAVAILABLE"

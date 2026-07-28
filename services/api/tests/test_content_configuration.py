from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import (
    AdminPrincipal,
    AdminRole,
    AdminSessionResolution,
    AdminSessionStatus,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    ContentLifecycle,
)
from kefe_api.modules.content_configuration.bootstrap import build_default_content_configuration
from kefe_api.modules.content_configuration.in_memory import InMemoryContentConfigurationRepository
from kefe_api.modules.content_configuration.models import (
    CapabilityDefinition,
    ContentConfigLifecycle,
    FlowStepDefinition,
    FlowTemplateDefinition,
    TopicItem,
)
from kefe_api.modules.content_configuration.service import ContentConfigurationService

NOW = datetime.now(UTC)


class StaticResolver:
    def resolve(self, session_token: str) -> AdminSessionResolution:
        return AdminSessionResolution(AdminSessionStatus.INVALID)

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None:
        return None


def _security() -> AdminSecurityService:
    return AdminSecurityService(
        session_resolver=StaticResolver(),
        policy=default_admin_security_policy(),
    )


def _principal(role: AdminRole) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({role}),
        direct_capabilities=frozenset(),
        authenticated_at=NOW - timedelta(hours=1),
        mfa_satisfied_at=NOW - timedelta(hours=1),
        step_up_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=10),
        last_seen_at=NOW - timedelta(minutes=1),
    )


def _service() -> ContentConfigurationService:
    repository = InMemoryContentConfigurationRepository(build_default_content_configuration())
    return ContentConfigurationService(repository=repository, security=_security())


def _case(**changes) -> AuthoringCaseVersion:
    base = AuthoringCaseVersion(
        id=uuid4(),
        case_id=uuid4(),
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="Configuration review test",
        summary="Configuration review derivation test.",
        base_format_code="TODAY",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(),
    )
    return replace(base, **changes)


def test_taxonomy_manager_can_publish_new_immutable_configuration() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)

    original = service.current()
    draft = service.create_draft_from_current(principal)
    assert draft.state is ContentConfigLifecycle.DRAFT
    assert draft.version_no == original.version_no + 1
    assert draft.cloned_from_version_id == original.id

    published = service.publish(principal, draft.id)
    assert published.state is ContentConfigLifecycle.PUBLISHED
    assert service.current().id == published.id

    versions = service.list_versions(principal)
    previous = next(item for item in versions if item.id == original.id)
    assert previous.state is ContentConfigLifecycle.SUPERSEDED

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, published)
    assert exc.value.code == "CONTENT_CONFIG_IMMUTABLE"


def test_rollback_creates_new_draft_without_rewriting_history() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    original = service.current()

    second = service.create_draft_from_current(principal)
    service.publish(principal, second.id)

    rollback = service.create_rollback_draft(
        principal,
        original.id,
        rationale="Restore known-good taxonomy after editorial validation issue",
    )
    assert rollback.state is ContentConfigLifecycle.DRAFT
    assert rollback.id not in {original.id, second.id}
    assert rollback.cloned_from_version_id == original.id
    assert service.current().id == second.id


def test_non_taxonomy_admin_cannot_manage_configuration() -> None:
    service = _service()
    editor = _principal(AdminRole.EDITOR)

    with pytest.raises(DomainError) as exc:
        service.create_draft_from_current(editor)
    assert exc.value.code == "ADMIN_FORBIDDEN"


def test_topic_must_reference_known_domain() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    invalid = replace(
        draft,
        topics=(
            TopicItem(
                code="UNKNOWN_TOPIC",
                domain_code="MISSING_DOMAIN",
                label_key="topic.unknown",
            ),
        ),
    )

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, invalid)
    assert exc.value.code == "CONTENT_CONFIG_TOPIC_DOMAIN_UNKNOWN"


def test_default_configuration_composes_materially_different_flows() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)

    by_code = {flow.code: flow for flow in draft.flow_templates}
    standard = by_code["STANDARD_COMMIT_REVEAL"]
    retest = by_code["PRINCIPLE_CONTEXT_RETEST"]

    assert standard.entry_step_code == "CONTEXT"
    assert retest.entry_step_code == "PRINCIPLE"
    assert {step.primitive_code for step in standard.steps} <= draft.enabled_primitive_codes
    assert {step.primitive_code for step in retest.steps} <= draft.enabled_primitive_codes
    assert any(
        "PRINCIPLE_FIRST" in step.capability_codes for step in retest.steps
    )
    assert all(
        "PRINCIPLE_FIRST" not in step.capability_codes for step in standard.steps
    )

    saved = service.save_draft(principal, draft)
    assert saved.flow_templates == draft.flow_templates


def test_capability_compatibility_must_reference_known_primitive() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    first = draft.capabilities[0]
    invalid_capability = replace(
        first,
        compatible_primitive_codes=frozenset({"MISSING_PRIMITIVE"}),
    )
    invalid = replace(
        draft,
        capabilities=(invalid_capability, *draft.capabilities[1:]),
    )

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, invalid)
    assert exc.value.code == "CONTENT_CONFIG_REFERENCE_UNKNOWN"


def test_flow_step_rejects_incompatible_capability() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    flow = draft.flow_templates[0]
    context_step = flow.steps[0]
    invalid_step = replace(
        context_step,
        capability_codes=("PRINCIPLE_FIRST",),
    )
    invalid_flow = replace(flow, steps=(invalid_step, *flow.steps[1:]))
    invalid = replace(
        draft,
        flow_templates=(invalid_flow, *draft.flow_templates[1:]),
    )

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, invalid)
    assert exc.value.code == "CONTENT_CONFIG_CAPABILITY_INCOMPATIBLE"


def test_flow_transition_target_must_exist_in_same_template() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    flow = draft.flow_templates[0]
    first_step = flow.steps[0]
    invalid_step = replace(first_step, next_step_codes=("MISSING_STEP",))
    invalid_flow = replace(flow, steps=(invalid_step, *flow.steps[1:]))
    invalid = replace(
        draft,
        flow_templates=(invalid_flow, *draft.flow_templates[1:]),
    )

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, invalid)
    assert exc.value.code == "CONTENT_CONFIG_REFERENCE_UNKNOWN"


def test_flow_requires_terminal_step() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    flow = FlowTemplateDefinition(
        code="NO_TERMINAL",
        version_no=1,
        label_key="flow.no_terminal",
        entry_step_code="A",
        steps=(
            FlowStepDefinition(
                code="A",
                primitive_code="CONTEXT",
                next_step_codes=("B",),
            ),
            FlowStepDefinition(
                code="B",
                primitive_code="DECISION",
                capability_codes=("COMMIT_FIRST",),
                next_step_codes=("A",),
            ),
        ),
    )
    invalid = replace(draft, flow_templates=(*draft.flow_templates, flow))

    with pytest.raises(DomainError) as exc:
        service.save_draft(principal, invalid)
    assert exc.value.code == "CONTENT_CONFIG_FLOW_INVALID"


def test_unrestricted_capability_can_be_registered_without_runtime_case_type() -> None:
    service = _service()
    principal = _principal(AdminRole.TAXONOMY_MANAGER)
    draft = service.create_draft_from_current(principal)
    capability = CapabilityDefinition(
        code="FUTURE_GENERIC_CAPABILITY",
        label_key="capability.future_generic_capability",
        compatible_primitive_codes=frozenset(),
    )
    updated = replace(draft, capabilities=(*draft.capabilities, capability))

    saved = service.save_draft(principal, updated)
    assert "FUTURE_GENERIC_CAPABILITY" in saved.enabled_capability_codes


def test_review_requirements_are_derived_server_side() -> None:
    service = _service()

    assert service.derive_required_review_modes(_case()) == frozenset()
    assert service.derive_required_review_modes(
        _case(is_fact_bearing=True),
    ) == frozenset({"SOURCE_VERIFICATION"})
    assert service.derive_required_review_modes(
        _case(content_risk="L2"),
    ) == frozenset({"RISK_REVIEW"})
    assert service.derive_required_review_modes(
        _case(primary_domain_code="CIVIC_POLITICS"),
    ) == frozenset({"CIVIC_REVIEW"})
    assert service.derive_required_review_modes(
        _case(
            content_risk="L3",
            is_real_event=True,
            primary_domain_code="CIVIC_POLITICS",
        ),
    ) == frozenset(
        {
            "EDITORIAL",
            "SOURCE_VERIFICATION",
            "RISK_REVIEW",
            "CIVIC_REVIEW",
        }
    )

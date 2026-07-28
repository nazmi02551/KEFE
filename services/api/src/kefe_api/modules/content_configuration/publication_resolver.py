from __future__ import annotations

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    PublicationConfigurationResolution,
    ResolvedFlowDefinition,
    ResolvedFlowStep,
)
from kefe_api.modules.content_configuration.ports import ContentConfigurationRepository


class ContentConfigurationPublicationResolver:
    """Resolve a CaseVersion against one immutable published configuration snapshot."""

    def __init__(self, repository: ContentConfigurationRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        version: AuthoringCaseVersion,
    ) -> PublicationConfigurationResolution:
        snapshot = self._repository.current_published()
        if snapshot is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_PUBLISHED",
                "No published content configuration is available",
                503,
            )

        failures: list[dict[str, str]] = []
        if version.primary_domain_code not in snapshot.enabled_domain_codes:
            failures.append(
                {
                    "code": "CONTENT_CONFIG_DOMAIN_UNAVAILABLE",
                    "detail": "CaseVersion primary Domain is unavailable in published configuration",
                    "path": "primary_domain_code",
                }
            )

        if version.base_format_code not in snapshot.enabled_base_format_codes:
            failures.append(
                {
                    "code": "CONTENT_CONFIG_FORMAT_UNAVAILABLE",
                    "detail": "CaseVersion Base Format is unavailable in published configuration",
                    "path": "base_format_code",
                }
            )

        enabled_modifiers = snapshot.enabled_modifier_codes
        unavailable_modifiers = sorted(set(version.modifiers) - enabled_modifiers)
        if unavailable_modifiers:
            failures.append(
                {
                    "code": "CONTENT_CONFIG_MODIFIER_UNAVAILABLE",
                    "detail": "CaseVersion references unavailable Modifiers: "
                    + ", ".join(unavailable_modifiers),
                    "path": "modifiers",
                }
            )

        allowed_modifiers = snapshot.modifier_compatibility.get(version.base_format_code)
        if allowed_modifiers is not None:
            incompatible_modifiers = sorted(set(version.modifiers) - set(allowed_modifiers))
            if incompatible_modifiers:
                failures.append(
                    {
                        "code": "CONTENT_CONFIG_MODIFIER_INCOMPATIBLE",
                        "detail": "CaseVersion Modifiers are incompatible with Base Format: "
                        + ", ".join(incompatible_modifiers),
                        "path": "modifiers",
                    }
                )

        flow = next(
            (
                item
                for item in snapshot.flow_templates
                if item.enabled
                and item.code == version.flow_template_code
                and item.version_no == version.flow_template_version_no
            ),
            None,
        )
        if flow is None:
            failures.append(
                {
                    "code": "CONTENT_CONFIG_FLOW_UNAVAILABLE",
                    "detail": "Selected FlowTemplateVersion is unavailable in published configuration",
                    "path": "flow_template_code",
                }
            )

        if failures:
            raise DomainError(
                "CONTENT_PUBLICATION_INVALID",
                "CaseVersion is incompatible with the published content configuration",
                422,
                meta={"failures": failures},
            )

        assert flow is not None
        enabled_primitives = snapshot.enabled_primitive_codes
        enabled_capabilities = snapshot.enabled_capability_codes
        capability_by_code = {item.code: item for item in snapshot.capabilities}

        resolved_steps: list[ResolvedFlowStep] = []
        for step in flow.steps:
            if step.primitive_code not in enabled_primitives:
                raise self._flow_invalid(
                    flow.code,
                    step.code,
                    "Flow Step Primitive is unavailable in published configuration",
                )
            for capability_code in step.capability_codes:
                if capability_code not in enabled_capabilities:
                    raise self._flow_invalid(
                        flow.code,
                        step.code,
                        f"Flow Step Capability {capability_code} is unavailable",
                    )
                capability = capability_by_code[capability_code]
                compatible = capability.compatible_primitive_codes
                if compatible and step.primitive_code not in compatible:
                    raise self._flow_invalid(
                        flow.code,
                        step.code,
                        f"Capability {capability_code} is incompatible with Primitive {step.primitive_code}",
                    )
            resolved_steps.append(
                ResolvedFlowStep(
                    code=step.code,
                    primitive_code=step.primitive_code,
                    capability_codes=step.capability_codes,
                    next_step_codes=step.next_step_codes,
                    payload_schema_ref=step.payload_schema_ref,
                )
            )

        return PublicationConfigurationResolution(
            content_configuration_id=snapshot.id,
            content_configuration_version_no=snapshot.version_no,
            resolved_flow=ResolvedFlowDefinition(
                template_code=flow.code,
                template_version_no=flow.version_no,
                entry_step_code=flow.entry_step_code,
                steps=tuple(resolved_steps),
            ),
        )

    @staticmethod
    def _flow_invalid(flow_code: str, step_code: str, detail: str) -> DomainError:
        return DomainError(
            "CONTENT_PUBLICATION_INVALID",
            "Resolved Flow failed publication validation",
            422,
            meta={
                "failures": [
                    {
                        "code": "CONTENT_CONFIG_FLOW_INVALID",
                        "detail": detail,
                        "path": f"flow_templates.{flow_code}.{step_code}",
                    }
                ]
            },
        )

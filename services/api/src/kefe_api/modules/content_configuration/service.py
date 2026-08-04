from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.models import AuthoringCaseVersion
from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
    FlowTemplateDefinition,
)
from kefe_api.modules.content_configuration.policy import derive_required_review_modes
from kefe_api.modules.content_configuration.ports import ContentConfigurationRepository


class ContentConfigurationService:
    def __init__(
        self,
        *,
        repository: ContentConfigurationRepository,
        security: AdminSecurityService,
    ) -> None:
        self._repository = repository
        self._security = security

    def current(self) -> ContentConfigurationSnapshot:
        snapshot = self._repository.current_published()
        if snapshot is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_PUBLISHED",
                "No published content configuration is available",
                503,
            )
        return snapshot

    def list_versions(
        self,
        principal: AdminPrincipal,
    ) -> tuple[ContentConfigurationSnapshot, ...]:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        return self._repository.list_versions()

    def create_draft_from_current(
        self,
        principal: AdminPrincipal,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        current = self.current()
        draft = replace(
            current,
            id=uuid4(),
            version_no=self._repository.next_version_no(),
            state=ContentConfigLifecycle.DRAFT,
            created_by=principal.audit_actor_ref,
            created_at=datetime.now(UTC),
            published_at=None,
            cloned_from_version_id=current.id,
        )
        audit = ContentConfigurationAuditEntry.create(
            snapshot=draft,
            actor_ref=principal.audit_actor_ref,
            command="CREATE_DRAFT_FROM_CURRENT",
            previous_state=None,
            new_state=ContentConfigLifecycle.DRAFT,
        )
        self._repository.save_draft(draft, audit=audit)
        return draft

    def save_draft(
        self,
        principal: AdminPrincipal,
        snapshot: ContentConfigurationSnapshot,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        current = self._repository.get(snapshot.id)
        if current is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_FOUND",
                "Content configuration was not found",
                404,
            )
        if current.state is not ContentConfigLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_CONFIG_IMMUTABLE",
                "Published or superseded content configuration is immutable",
                409,
            )
        if snapshot.version_no != current.version_no:
            raise DomainError(
                "CONTENT_CONFIG_VERSION_MISMATCH",
                "Content configuration version number cannot be changed",
                409,
            )
        self._validate_snapshot(snapshot)
        updated = replace(
            snapshot,
            state=ContentConfigLifecycle.DRAFT,
            created_by=current.created_by,
            created_at=current.created_at,
            published_at=None,
            cloned_from_version_id=current.cloned_from_version_id,
        )
        audit = ContentConfigurationAuditEntry.create(
            snapshot=updated,
            actor_ref=principal.audit_actor_ref,
            command="SAVE_DRAFT",
            previous_state=ContentConfigLifecycle.DRAFT,
            new_state=ContentConfigLifecycle.DRAFT,
        )
        self._repository.replace_draft(updated, audit=audit)
        return updated

    def publish(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        current = self._repository.get(version_id)
        if current is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_FOUND",
                "Content configuration was not found",
                404,
            )
        if current.state is not ContentConfigLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_CONFIG_NOT_DRAFT",
                "Only a DRAFT content configuration can be published",
                409,
            )
        self._validate_snapshot(current)
        published = current.with_state(
            ContentConfigLifecycle.PUBLISHED,
            published_at=datetime.now(UTC),
        )
        audit = ContentConfigurationAuditEntry.create(
            snapshot=published,
            actor_ref=principal.audit_actor_ref,
            command="PUBLISH",
            previous_state=ContentConfigLifecycle.DRAFT,
            new_state=ContentConfigLifecycle.PUBLISHED,
        )
        result, _ = self._repository.publish_atomically(
            snapshot=published,
            audit=audit,
        )
        return result

    def create_rollback_draft(
        self,
        principal: AdminPrincipal,
        source_version_id: UUID,
        *,
        rationale: str,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        source = self._repository.get(source_version_id)
        if source is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_FOUND",
                "Content configuration was not found",
                404,
            )
        if source.state not in {
            ContentConfigLifecycle.PUBLISHED,
            ContentConfigLifecycle.SUPERSEDED,
        }:
            raise DomainError(
                "CONTENT_CONFIG_ROLLBACK_SOURCE_INVALID",
                "Rollback source must be a previously published configuration",
                409,
            )
        draft = replace(
            source,
            id=uuid4(),
            version_no=self._repository.next_version_no(),
            state=ContentConfigLifecycle.DRAFT,
            created_by=principal.audit_actor_ref,
            created_at=datetime.now(UTC),
            published_at=None,
            cloned_from_version_id=source.id,
        )
        audit = ContentConfigurationAuditEntry.create(
            snapshot=draft,
            actor_ref=principal.audit_actor_ref,
            command="CREATE_ROLLBACK_DRAFT",
            previous_state=None,
            new_state=ContentConfigLifecycle.DRAFT,
            rationale=rationale,
        )
        self._repository.save_draft(draft, audit=audit)
        return draft

    def derive_required_review_modes(
        self,
        version: AuthoringCaseVersion,
    ) -> frozenset[str]:
        return derive_required_review_modes(version)

    @staticmethod
    def _validate_snapshot(snapshot: ContentConfigurationSnapshot) -> None:
        domain_codes = [item.code for item in snapshot.domains]
        format_codes = [item.code for item in snapshot.base_formats]
        modifier_codes = [item.code for item in snapshot.modifiers]
        primitive_codes = [item.code for item in snapshot.primitives]
        capability_codes = [item.code for item in snapshot.capabilities]
        flow_keys = [(item.code, item.version_no) for item in snapshot.flow_templates]

        for label, values in (
            ("domain", domain_codes),
            ("base format", format_codes),
            ("modifier", modifier_codes),
            ("primitive", primitive_codes),
            ("capability", capability_codes),
            ("flow template version", flow_keys),
        ):
            if len(values) != len(set(values)):
                raise DomainError(
                    "CONTENT_CONFIG_DUPLICATE_CODE",
                    f"Duplicate {label} identity exists in content configuration",
                    422,
                )

        domain_set = set(domain_codes)
        for topic in snapshot.topics:
            if topic.domain_code not in domain_set:
                raise DomainError(
                    "CONTENT_CONFIG_TOPIC_DOMAIN_UNKNOWN",
                    "Topic references an unknown Domain",
                    422,
                    meta={"topic_code": topic.code, "domain_code": topic.domain_code},
                )

        enabled_formats = snapshot.enabled_base_format_codes
        enabled_modifiers = snapshot.enabled_modifier_codes
        for format_code, allowed in snapshot.modifier_compatibility.items():
            if format_code not in enabled_formats:
                raise DomainError(
                    "CONTENT_CONFIG_FORMAT_UNKNOWN",
                    "Modifier compatibility references an unavailable Base Format",
                    422,
                    meta={"base_format_code": format_code},
                )
            unknown = sorted(set(allowed) - enabled_modifiers)
            if unknown:
                raise DomainError(
                    "CONTENT_CONFIG_MODIFIER_UNKNOWN",
                    "Modifier compatibility references unavailable Modifiers",
                    422,
                    meta={"modifier_codes": unknown},
                )

        primitive_set = set(primitive_codes)
        enabled_primitive_set = snapshot.enabled_primitive_codes
        capability_set = set(capability_codes)
        enabled_capability_set = snapshot.enabled_capability_codes
        capability_by_code = {item.code: item for item in snapshot.capabilities}

        for capability in snapshot.capabilities:
            unknown = sorted(capability.compatible_primitive_codes - primitive_set)
            if unknown:
                raise DomainError(
                    "CONTENT_CONFIG_REFERENCE_UNKNOWN",
                    "Capability compatibility references unknown Primitives",
                    422,
                    meta={
                        "capability_code": capability.code,
                        "primitive_codes": unknown,
                    },
                )

        for flow in snapshot.flow_templates:
            if flow.version_no <= 0 or not flow.steps:
                raise DomainError(
                    "CONTENT_CONFIG_FLOW_INVALID",
                    "Flow Template must have a positive version and at least one Step",
                    422,
                    meta={"flow_code": flow.code, "version_no": flow.version_no},
                )

            step_codes = [step.code for step in flow.steps]
            if len(step_codes) != len(set(step_codes)):
                raise DomainError(
                    "CONTENT_CONFIG_DUPLICATE_CODE",
                    "Duplicate Step code exists within a Flow Template version",
                    422,
                    meta={"flow_code": flow.code, "version_no": flow.version_no},
                )
            step_set = set(step_codes)
            if flow.entry_step_code not in step_set:
                raise DomainError(
                    "CONTENT_CONFIG_FLOW_INVALID",
                    "Flow Template entry Step does not exist",
                    422,
                    meta={
                        "flow_code": flow.code,
                        "entry_step_code": flow.entry_step_code,
                    },
                )
            if not any(not step.next_step_codes for step in flow.steps):
                raise DomainError(
                    "CONTENT_CONFIG_FLOW_INVALID",
                    "Flow Template requires at least one terminal Step",
                    422,
                    meta={"flow_code": flow.code, "version_no": flow.version_no},
                )

            for step in flow.steps:
                available_primitives = (
                    enabled_primitive_set if flow.enabled else frozenset(primitive_set)
                )
                if step.primitive_code not in available_primitives:
                    raise DomainError(
                        "CONTENT_CONFIG_REFERENCE_UNKNOWN",
                        "Flow Step references an unavailable Primitive",
                        422,
                        meta={
                            "flow_code": flow.code,
                            "step_code": step.code,
                            "primitive_code": step.primitive_code,
                        },
                    )

                for capability_code in step.capability_codes:
                    available_capabilities = (
                        enabled_capability_set
                        if flow.enabled
                        else frozenset(capability_set)
                    )
                    if capability_code not in available_capabilities:
                        raise DomainError(
                            "CONTENT_CONFIG_REFERENCE_UNKNOWN",
                            "Flow Step references an unavailable Capability",
                            422,
                            meta={
                                "flow_code": flow.code,
                                "step_code": step.code,
                                "capability_code": capability_code,
                            },
                        )
                    capability = capability_by_code[capability_code]
                    compatible = capability.compatible_primitive_codes
                    if compatible and step.primitive_code not in compatible:
                        raise DomainError(
                            "CONTENT_CONFIG_CAPABILITY_INCOMPATIBLE",
                            "Capability is incompatible with the Flow Step Primitive",
                            422,
                            meta={
                                "flow_code": flow.code,
                                "step_code": step.code,
                                "primitive_code": step.primitive_code,
                                "capability_code": capability_code,
                            },
                        )

                unknown_next = sorted(set(step.next_step_codes) - step_set)
                if unknown_next:
                    raise DomainError(
                        "CONTENT_CONFIG_REFERENCE_UNKNOWN",
                        "Flow Step transition references unknown target Steps",
                        422,
                        meta={
                            "flow_code": flow.code,
                            "step_code": step.code,
                            "next_step_codes": unknown_next,
                        },
                    )

            unreachable = sorted(
                step_set - ContentConfigurationService._reachable_step_codes(flow)
            )
            if unreachable:
                raise DomainError(
                    "CONTENT_CONFIG_FLOW_UNREACHABLE",
                    "Every Flow Step must be reachable from the entry Step",
                    422,
                    meta={
                        "flow_code": flow.code,
                        "version_no": flow.version_no,
                        "step_codes": unreachable,
                    },
                )
            if ContentConfigurationService._flow_has_cycle(flow):
                raise DomainError(
                    "CONTENT_CONFIG_FLOW_CYCLIC",
                    "Flow Template topology must be acyclic",
                    422,
                    meta={"flow_code": flow.code, "version_no": flow.version_no},
                )

        for required_set_name, values in (
            ("risks", snapshot.risks),
            ("claim_states", snapshot.claim_states),
            ("source_kinds", snapshot.source_kinds),
            ("disclosure_levels", snapshot.disclosure_levels),
        ):
            if not values:
                raise DomainError(
                    "CONTENT_CONFIG_REQUIRED_SET_EMPTY",
                    f"{required_set_name} cannot be empty",
                    422,
                )

    @staticmethod
    def _reachable_step_codes(flow: FlowTemplateDefinition) -> set[str]:
        step_by_code = {step.code: step for step in flow.steps}
        reachable: set[str] = set()
        pending = [flow.entry_step_code]
        while pending:
            code = pending.pop()
            if code in reachable:
                continue
            reachable.add(code)
            pending.extend(step_by_code[code].next_step_codes)
        return reachable

    @staticmethod
    def _flow_has_cycle(flow: FlowTemplateDefinition) -> bool:
        step_by_code = {step.code: step for step in flow.steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(code: str) -> bool:
            if code in visiting:
                return True
            if code in visited:
                return False
            visiting.add(code)
            for next_code in step_by_code[code].next_step_codes:
                if visit(next_code):
                    return True
            visiting.remove(code)
            visited.add(code)
            return False

        return any(visit(code) for code in step_by_code)

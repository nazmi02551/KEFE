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

        for label, values in (
            ("domain", domain_codes),
            ("base format", format_codes),
            ("modifier", modifier_codes),
        ):
            if len(values) != len(set(values)):
                raise DomainError(
                    "CONTENT_CONFIG_DUPLICATE_CODE",
                    f"Duplicate {label} code exists in content configuration",
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

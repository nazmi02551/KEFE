from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)
from kefe_api.modules.content_configuration.ports import ContentConfigurationRepository
from kefe_api.modules.content_configuration.service import ContentConfigurationService


class SecuredContentConfigurationService:
    """Admin-only facade for composable Content Configuration management."""

    def __init__(
        self,
        *,
        configuration: ContentConfigurationService,
        repository: ContentConfigurationRepository,
        security: AdminSecurityService,
    ) -> None:
        self._configuration = configuration
        self._repository = repository
        self._security = security

    def current(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._configuration.current()

    def list_versions(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> tuple[ContentConfigurationSnapshot, ...]:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._repository.list_versions()

    def get_version(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._require_version(version_id)

    def draft_for_edit(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        version = self._require_version(version_id)
        if version.state is not ContentConfigLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_CONFIG_IMMUTABLE",
                "Published or superseded content configuration is immutable",
                409,
            )
        return version

    def create_draft_from_current(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._configuration.create_draft_from_current(principal)

    def save_draft(
        self,
        principal: AdminPrincipal,
        snapshot: ContentConfigurationSnapshot,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._configuration.save_draft(principal, snapshot)

    def publish(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._configuration.publish(principal, version_id)

    def create_rollback_draft(
        self,
        principal: AdminPrincipal,
        source_version_id: UUID,
        *,
        rationale: str,
        now: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE, now=now)
        return self._configuration.create_rollback_draft(
            principal,
            source_version_id,
            rationale=rationale,
        )

    def audit_trail(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> tuple[ContentConfigurationAuditEntry, ...]:
        self._security.authorize(principal, AdminCapability.AUDIT_READ, now=now)
        return self._repository.list_audit()

    def _require_version(self, version_id: UUID) -> ContentConfigurationSnapshot:
        version = self._repository.get(version_id)
        if version is None:
            raise DomainError(
                "CONTENT_CONFIG_NOT_FOUND",
                "Content configuration was not found",
                404,
            )
        return version

from __future__ import annotations

from uuid import UUID

from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_config.models import (
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)
from kefe_api.modules.content_config.service import ContentConfigurationService


class SecuredContentConfigurationService:
    def __init__(
        self,
        *,
        configuration: ContentConfigurationService,
        security: AdminSecurityService,
    ) -> None:
        self._configuration = configuration
        self._security = security

    def current(self, principal: AdminPrincipal) -> ContentConfigurationSnapshot:
        return self._configuration.current()

    def create_draft(self, principal: AdminPrincipal) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        return self._configuration.create_draft()

    def get(self, principal: AdminPrincipal, snapshot_id: UUID) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        return self._configuration.get(snapshot_id)

    def save_draft(
        self,
        principal: AdminPrincipal,
        snapshot_id: UUID,
        **changes: object,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        return self._configuration.save_draft(snapshot_id, **changes)  # type: ignore[arg-type]

    def publish(
        self,
        principal: AdminPrincipal,
        snapshot_id: UUID,
    ) -> ContentConfigurationSnapshot:
        self._security.authorize(principal, AdminCapability.TAXONOMY_MANAGE)
        return self._configuration.publish(
            snapshot_id,
            actor_ref=principal.audit_actor_ref,
        )

    def audit(self, principal: AdminPrincipal) -> tuple[ContentConfigurationAuditEntry, ...]:
        self._security.authorize(principal, AdminCapability.AUDIT_READ)
        return self._configuration.audit()

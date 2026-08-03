from __future__ import annotations

from datetime import datetime

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    PublicFeedActivationCatalogEntry,
    PublicFeedActivationCatalogRepository,
)


class SecuredPublicFeedActivationCatalogService:
    def __init__(
        self,
        *,
        repository: PublicFeedActivationCatalogRepository,
        security: AdminSecurityService,
    ) -> None:
        self._repository = repository
        self._security = security

    def list_entries(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        after_activation_code: str | None = None,
        now: datetime | None = None,
    ) -> tuple[PublicFeedActivationCatalogEntry, ...]:
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_VERIFY,
            now=now,
        )
        return self._repository.list_entries(
            limit=limit,
            after_activation_code=after_activation_code,
        )

    def detail(
        self,
        principal: AdminPrincipal,
        activation_code: str,
        *,
        now: datetime | None = None,
    ) -> PublicFeedActivationCatalogEntry:
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_VERIFY,
            now=now,
        )
        entry = self._repository.get_by_activation_code(activation_code)
        if entry is None:
            raise DomainError(
                "PUBLIC_FEED_ACTIVATION_CATALOG_NOT_FOUND",
                "Public feed activation catalog entry was not found",
                404,
            )
        return entry


__all__ = ["SecuredPublicFeedActivationCatalogService"]

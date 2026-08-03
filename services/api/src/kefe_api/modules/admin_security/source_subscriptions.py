from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hmac import compare_digest
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.rss_atom_subscription import (
    RssAtomSubscriptionActivationResult,
    RssAtomSubscriptionActivationService,
    RssAtomSubscriptionManifest,
    RssAtomSubscriptionManifestRegistry,
)

MAX_ADMIN_SUBSCRIPTION_ITEMS = 256


@dataclass(frozen=True, slots=True)
class AdminRssAtomSubscriptionView:
    subscription_code: str
    adapter_code: str
    external_locator: str
    interval_seconds: int
    max_dispatch_attempts: int
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_redirect_hops: int
    locale: str | None
    jurisdiction_code: str | None
    configuration_hash: str

    @classmethod
    def from_manifest(
        cls,
        manifest: RssAtomSubscriptionManifest,
    ) -> AdminRssAtomSubscriptionView:
        return cls(
            subscription_code=manifest.subscription_code,
            adapter_code=manifest.adapter_code,
            external_locator=manifest.external_locator,
            interval_seconds=manifest.interval_seconds,
            max_dispatch_attempts=manifest.max_dispatch_attempts,
            quota_limit=manifest.quota_limit,
            quota_window_seconds=manifest.quota_window_seconds,
            failure_threshold=manifest.failure_threshold,
            circuit_open_seconds=manifest.circuit_open_seconds,
            permit_ttl_seconds=manifest.permit_ttl_seconds,
            connect_timeout_ms=manifest.connect_timeout_ms,
            read_timeout_ms=manifest.read_timeout_ms,
            total_timeout_ms=manifest.total_timeout_ms,
            max_redirect_hops=manifest.max_redirect_hops,
            locale=manifest.locale,
            jurisdiction_code=manifest.jurisdiction_code,
            configuration_hash=manifest.configuration_hash,
        )


@dataclass(frozen=True, slots=True)
class AdminRssAtomActivationView:
    subscription_code: str
    adapter_code: str
    configuration_hash: str
    capability_lifecycle: str
    circuit_state: str
    schedule_id: UUID
    schedule_state: str
    next_due_at: datetime

    @classmethod
    def from_result(
        cls,
        *,
        manifest: RssAtomSubscriptionManifest,
        result: RssAtomSubscriptionActivationResult,
    ) -> AdminRssAtomActivationView:
        return cls(
            subscription_code=result.subscription_code,
            adapter_code=result.adapter_code,
            configuration_hash=manifest.configuration_hash,
            capability_lifecycle=result.provider_capability.lifecycle_state.value,
            circuit_state=result.provider_capability.circuit_state.value,
            schedule_id=result.schedule.id,
            schedule_state=result.schedule.state.value,
            next_due_at=result.schedule.next_due_at,
        )


class SecuredRssAtomSubscriptionService:
    def __init__(
        self,
        *,
        registry: RssAtomSubscriptionManifestRegistry,
        activation: RssAtomSubscriptionActivationService,
        security: AdminSecurityService,
    ) -> None:
        self._registry = registry
        self._activation = activation
        self._security = security

    def list_subscriptions(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> tuple[AdminRssAtomSubscriptionView, ...]:
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_SUBSCRIPTION_READ,
            now=now,
        )
        manifests = self._registry.manifests
        if len(manifests) > MAX_ADMIN_SUBSCRIPTION_ITEMS:
            raise DomainError(
                "SOURCE_SUBSCRIPTION_INVENTORY_LIMIT_EXCEEDED",
                "Source subscription inventory exceeds the supported limit",
                409,
            )
        return tuple(
            AdminRssAtomSubscriptionView.from_manifest(manifest)
            for manifest in manifests
        )

    def activate(
        self,
        principal: AdminPrincipal,
        *,
        subscription_code: str,
        expected_configuration_hash: str,
        first_due_at: datetime,
        now: datetime | None = None,
    ) -> AdminRssAtomActivationView:
        current = now or datetime.now(UTC)
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_SUBSCRIPTION_ACTIVATE,
            now=current,
        )
        if first_due_at.tzinfo is None or first_due_at.utcoffset() != UTC.utcoffset(
            first_due_at
        ):
            raise DomainError(
                "SOURCE_SUBSCRIPTION_FIRST_DUE_INVALID",
                "First due timestamp must be timezone-aware UTC",
                422,
            )
        try:
            manifest = self._registry.get(subscription_code)
        except (KeyError, ValueError) as exc:
            raise DomainError(
                "SOURCE_SUBSCRIPTION_NOT_FOUND",
                "Source subscription was not found",
                404,
            ) from exc
        if not compare_digest(
            expected_configuration_hash,
            manifest.configuration_hash,
        ):
            raise DomainError(
                "SOURCE_SUBSCRIPTION_CONFIGURATION_STALE",
                "Source subscription configuration has changed",
                409,
                meta={"current_configuration_hash": manifest.configuration_hash},
            )
        result = self._activation.activate(
            subscription_code=manifest.subscription_code,
            first_due_at=first_due_at,
            activated_at=current,
        )
        return AdminRssAtomActivationView.from_result(
            manifest=manifest,
            result=result,
        )


__all__ = [
    "AdminRssAtomActivationView",
    "AdminRssAtomSubscriptionView",
    "MAX_ADMIN_SUBSCRIPTION_ITEMS",
    "SecuredRssAtomSubscriptionService",
]

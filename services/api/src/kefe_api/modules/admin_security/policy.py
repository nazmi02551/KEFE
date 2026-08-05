from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from kefe_api.modules.admin_security.models import AdminCapability, AdminRole


@dataclass(frozen=True, slots=True)
class AdminSecurityPolicy:
    role_capabilities: dict[AdminRole, frozenset[AdminCapability]]
    step_up_capabilities: frozenset[AdminCapability]
    absolute_lifetime: timedelta
    idle_timeout: timedelta
    step_up_freshness: timedelta
    reviewer_must_differ_from_submitter: bool = True
    publisher_must_differ_from_approver: bool = True

    def capabilities_for_roles(
        self,
        roles: frozenset[AdminRole],
    ) -> frozenset[AdminCapability]:
        granted: set[AdminCapability] = set()
        for role in roles:
            granted.update(self.role_capabilities.get(role, frozenset()))
        return frozenset(granted)


def default_admin_security_policy() -> AdminSecurityPolicy:
    return AdminSecurityPolicy(
        role_capabilities={
            AdminRole.EDITOR: frozenset(
                {
                    AdminCapability.CONTENT_CREATE,
                    AdminCapability.CONTENT_PROJECT,
                    AdminCapability.CONTENT_EDIT,
                    AdminCapability.CONTENT_SUBMIT_REVIEW,
                    AdminCapability.MEDIA_ASSET_READ,
                    AdminCapability.MEDIA_ASSET_MANAGE,
                }
            ),
            AdminRole.REVIEWER: frozenset(
                {
                    AdminCapability.CONTENT_REVIEW,
                    AdminCapability.CONTENT_MODERATE,
                    AdminCapability.SOURCE_VERIFY,
                    AdminCapability.SOURCE_MANAGE,
                    AdminCapability.MEDIA_ASSET_READ,
                    AdminCapability.RISK_REVIEW,
                    AdminCapability.AUDIT_READ,
                    AdminCapability.OPERATIONAL_REPORT_READ,
                }
            ),
            AdminRole.PUBLISHER: frozenset(
                {
                    AdminCapability.CONTENT_PUBLISH,
                    AdminCapability.CONTENT_WITHDRAW,
                    AdminCapability.MEDIA_ASSET_READ,
                    AdminCapability.AUDIT_READ,
                    AdminCapability.OPERATIONAL_REPORT_READ,
                }
            ),
            AdminRole.TAXONOMY_MANAGER: frozenset(
                {
                    AdminCapability.TAXONOMY_MANAGE,
                    AdminCapability.AUDIT_READ,
                }
            ),
            AdminRole.ACCESS_ADMIN: frozenset(
                {
                    AdminCapability.ADMIN_ACCESS_MANAGE,
                    AdminCapability.SOURCE_APPROVE,
                    AdminCapability.SOURCE_ACTIVATE,
                    AdminCapability.MEDIA_ASSET_READ,
                    AdminCapability.MEDIA_ASSET_MANAGE,
                    AdminCapability.AUDIT_READ,
                    AdminCapability.OPERATIONAL_REPORT_READ,
                }
            ),
        },
        step_up_capabilities=frozenset(
            {
                AdminCapability.CONTENT_MODERATE,
                AdminCapability.CONTENT_PUBLISH,
                AdminCapability.CONTENT_WITHDRAW,
                AdminCapability.SOURCE_APPROVE,
                AdminCapability.SOURCE_ACTIVATE,
                AdminCapability.MEDIA_ASSET_MANAGE,
                AdminCapability.ADMIN_ACCESS_MANAGE,
            }
        ),
        absolute_lifetime=timedelta(hours=12),
        idle_timeout=timedelta(minutes=30),
        step_up_freshness=timedelta(minutes=15),
        reviewer_must_differ_from_submitter=True,
        publisher_must_differ_from_approver=True,
    )

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
                }
            ),
            AdminRole.REVIEWER: frozenset(
                {
                    AdminCapability.CONTENT_REVIEW,
                    AdminCapability.SOURCE_VERIFY,
                    AdminCapability.RISK_REVIEW,
                    AdminCapability.AUDIT_READ,
                }
            ),
            AdminRole.PUBLISHER: frozenset(
                {
                    AdminCapability.CONTENT_PUBLISH,
                    AdminCapability.CONTENT_WITHDRAW,
                    AdminCapability.AUDIT_READ,
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
                    AdminCapability.AUDIT_READ,
                }
            ),
        },
        step_up_capabilities=frozenset(
            {
                AdminCapability.CONTENT_PUBLISH,
                AdminCapability.CONTENT_WITHDRAW,
                AdminCapability.ADMIN_ACCESS_MANAGE,
            }
        ),
        absolute_lifetime=timedelta(hours=12),
        idle_timeout=timedelta(minutes=30),
        step_up_freshness=timedelta(minutes=15),
        reviewer_must_differ_from_submitter=True,
    )

from __future__ import annotations

from uuid import UUID

from kefe_api.modules.admin_operational_reports.models import (
    AdminOperationalReportSnapshot,
)
from kefe_api.modules.admin_operational_reports.service import (
    AdminOperationalReportsService,
)
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.identity.otp_delivery_health import OtpDeliveryAlertRecord


class SecuredAdminOperationalReportsService:
    def __init__(
        self,
        *,
        reports: AdminOperationalReportsService,
        security: AdminSecurityService,
    ) -> None:
        self._reports = reports
        self._security = security

    def snapshot(
        self,
        principal: AdminPrincipal,
    ) -> AdminOperationalReportSnapshot:
        self._security.authorize(
            principal,
            AdminCapability.OPERATIONAL_REPORT_READ,
        )
        return self._reports.snapshot()

    def otp_delivery_alert_candidates(
        self,
        principal: AdminPrincipal,
        *,
        acknowledged: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[OtpDeliveryAlertRecord, ...]:
        self._security.authorize(
            principal,
            AdminCapability.OPERATIONAL_REPORT_READ,
        )
        return self._reports.otp_delivery_alert_candidates(
            acknowledged=acknowledged,
            limit=limit,
            offset=offset,
        )

    def acknowledge_otp_delivery_alert(
        self,
        principal: AdminPrincipal,
        *,
        candidate_id: UUID,
    ) -> OtpDeliveryAlertRecord:
        self._security.authorize(
            principal,
            AdminCapability.OPERATIONAL_ALERT_ACKNOWLEDGE,
        )
        return self._reports.acknowledge_otp_delivery_alert(
            candidate_id=candidate_id,
            actor_ref=principal.audit_actor_ref,
        )

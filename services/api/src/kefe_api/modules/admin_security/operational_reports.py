from __future__ import annotations

from kefe_api.modules.admin_operational_reports.models import (
    AdminOperationalReportSnapshot,
)
from kefe_api.modules.admin_operational_reports.service import (
    AdminOperationalReportsService,
)
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService


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

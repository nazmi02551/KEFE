from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionResult,
)
from kefe_api.modules.editorial_projection.service import EditorialProjectionService


class SecuredEditorialProjectionService:
    """Admin facade that derives projection audit identity from the session principal."""

    def __init__(
        self,
        *,
        projection: EditorialProjectionService,
        security: AdminSecurityService,
    ) -> None:
        self._projection = projection
        self._security = security

    def project(
        self,
        principal: AdminPrincipal,
        *,
        candidate_proposal_id: UUID,
        proposal_review_decision_id: UUID,
        profile_code: str,
        profile_version: int,
        idempotency_key: str,
        explicit_flow_template_code: str | None = None,
        explicit_flow_template_version: int | None = None,
        now: datetime | None = None,
    ) -> EditorialProjectionResult:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_PROJECT,
            now=now,
        )
        command = EditorialProjectionCommand(
            candidate_proposal_id=candidate_proposal_id,
            proposal_review_decision_id=proposal_review_decision_id,
            profile_code=profile_code,
            profile_version=profile_version,
            idempotency_key=idempotency_key,
            requested_by_admin_ref=principal.audit_actor_ref,
            explicit_flow_template_code=explicit_flow_template_code,
            explicit_flow_template_version=explicit_flow_template_version,
        )
        return self._projection.project(command)

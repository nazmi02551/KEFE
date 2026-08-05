from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.router import write_principal
from kefe_api.modules.community_reason.models import CommunityReasonModeration
from kefe_api.modules.community_reason.moderation_operations_router import (
    router as moderation_operations_router,
)
from kefe_api.modules.community_reason.service import CommunityReasonService

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class ModerateCommunityReasonRequest(BaseModel):
    state: CommunityReasonModeration


class ModerateCommunityReasonResponse(BaseModel):
    reason_id: UUID
    moderation_state: str


def get_service(request: Request) -> CommunityReasonService:
    return request.app.state.community_reason_service


PrincipalDep = Annotated[AdminPrincipal, Depends(write_principal)]
ServiceDep = Annotated[CommunityReasonService, Depends(get_service)]


@router.post(
    "/community-reasons/{reason_id}/moderation",
    response_model=ModerateCommunityReasonResponse,
)
def moderate_reason(
    reason_id: UUID,
    body: ModerateCommunityReasonRequest,
    principal: PrincipalDep,
    service: ServiceDep,
    request: Request,
) -> ModerateCommunityReasonResponse:
    request.app.state.admin_security_service.authorize(
        principal,
        AdminCapability.CONTENT_MODERATE,
    )
    rationale = request.headers.get("X-KEFE-Moderation-Rationale", "")
    decision = service.moderate(
        reason_id=reason_id,
        state=body.state,
        actor_ref=principal.audit_actor_ref,
        rationale=rationale,
    )
    return ModerateCommunityReasonResponse(
        reason_id=decision.reason.id,
        moderation_state=decision.reason.moderation_state.value,
    )


router.include_router(moderation_operations_router)

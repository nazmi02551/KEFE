from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request

from kefe_api.modules.identity.models import ActorPrincipal
from kefe_api.modules.identity.service import IdentityService


def get_identity_service(request: Request) -> IdentityService:
    return request.app.state.identity_service


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def get_principal(
    authorization: AuthorizationHeader,
    service: IdentityServiceDep,
) -> ActorPrincipal:
    return service.authenticate(authorization)


PrincipalDep = Annotated[ActorPrincipal, Depends(get_principal)]

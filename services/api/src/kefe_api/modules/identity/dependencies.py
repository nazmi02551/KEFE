from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from kefe_api.modules.identity.admission import GuestAdmissionGuard
from kefe_api.modules.identity.models import ActorPrincipal, TokenResolution
from kefe_api.modules.identity.service import IdentityService

_bearer = HTTPBearer(auto_error=False)


def get_identity_service(request: Request) -> IdentityService:
    return request.app.state.identity_service


def get_guest_admission_guard(request: Request) -> GuestAdmissionGuard:
    return request.app.state.guest_admission_guard


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
GuestAdmissionGuardDep = Annotated[GuestAdmissionGuard, Depends(get_guest_admission_guard)]
BearerCredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Security(_bearer),
]


def get_authorization(credentials: BearerCredentialsDep) -> str | None:
    if credentials is None:
        return None
    return f"{credentials.scheme} {credentials.credentials}"


AuthorizationDep = Annotated[str | None, Depends(get_authorization)]


def get_principal(
    authorization: AuthorizationDep,
    service: IdentityServiceDep,
) -> ActorPrincipal:
    return service.authenticate(authorization)


def get_guest_merge_authorization(
    authorization: AuthorizationDep,
    service: IdentityServiceDep,
) -> TokenResolution:
    return service.authenticate_guest_merge(authorization)


PrincipalDep = Annotated[ActorPrincipal, Depends(get_principal)]
GuestMergeAuthorizationDep = Annotated[
    TokenResolution,
    Depends(get_guest_merge_authorization),
]

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from kefe_api.modules.identity.dependencies import PrincipalDep
from kefe_api.modules.privacy.service import PrivacyService

router = APIRouter(prefix="/v1/me", tags=["Privacy"])


class PrivacyExportManifestResponse(BaseModel):
    dataset_counts: dict[str, int]
    total_records: int
    empty_datasets: list[str]


class PrivacyExportResponse(BaseModel):
    schema_version: str
    actor_id: UUID
    actor_kind: str
    generated_at: str
    retention: dict[str, Any]
    manifest: PrivacyExportManifestResponse
    product_data: dict[str, Any]
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PrivacyDeletionResponse(BaseModel):
    receipt_id: UUID
    actor_id: UUID
    actor_kind: str
    deleted_at: str
    policy_version: str
    private_data_deleted: bool
    aggregate_contributions_anonymized: bool


def get_service(request: Request) -> PrivacyService:
    return request.app.state.privacy_service


PrivacyServiceDep = Annotated[PrivacyService, Depends(get_service)]
DeleteConfirm = Annotated[str | None, Header(alias="X-KEFE-Delete-Confirm")]


@router.get("/privacy-export", response_model=PrivacyExportResponse)
def export_privacy(
    principal: PrincipalDep,
    service: PrivacyServiceDep,
) -> PrivacyExportResponse:
    bundle = service.export(principal)
    return PrivacyExportResponse(
        schema_version=bundle.schema_version,
        actor_id=bundle.actor_id,
        actor_kind=bundle.actor_kind,
        generated_at=bundle.generated_at.isoformat(),
        retention=bundle.retention,
        manifest=PrivacyExportManifestResponse(
            dataset_counts=bundle.manifest.dataset_counts,
            total_records=bundle.manifest.total_records,
            empty_datasets=list(bundle.manifest.empty_datasets),
        ),
        product_data=bundle.product_data,
        data_sha256=bundle.data_sha256,
    )


@router.delete("", response_model=PrivacyDeletionResponse)
def delete_me(
    principal: PrincipalDep,
    service: PrivacyServiceDep,
    confirm: DeleteConfirm = None,
) -> PrivacyDeletionResponse:
    receipt = service.delete(principal, confirmation=confirm)
    return PrivacyDeletionResponse(
        receipt_id=receipt.receipt_id,
        actor_id=receipt.actor_id,
        actor_kind=receipt.actor_kind,
        deleted_at=receipt.deleted_at.isoformat(),
        policy_version=receipt.policy_version,
        private_data_deleted=receipt.private_data_deleted,
        aggregate_contributions_anonymized=receipt.aggregate_contributions_anonymized,
    )

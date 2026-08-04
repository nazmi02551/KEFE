from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.case_builder_router import (
    CaseBuilderVersionResponse,
    _version_response,
)
from kefe_api.modules.admin_security.router import (
    AuthoringDep,
    ReadPrincipalDep,
    WritePrincipalDep,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    LifecycleAuditEntry,
)

router = APIRouter(
    prefix="/internal/admin/v1/content-reviews",
    tags=["Internal Admin Editorial Quality Review"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EditorialReviewQueueItem(StrictModel):
    version_id: UUID
    case_id: UUID
    version_no: int
    title: str
    content_risk: str
    primary_domain_code: str
    content_locale: str
    required_review_modes: list[str]
    created_at: datetime


class EditorialReviewQueueResponse(StrictModel):
    items: list[EditorialReviewQueueItem]
    next_offset: int | None


class EditorialReviewDetailResponse(StrictModel):
    version: CaseBuilderVersionResponse
    submitter_actor_ref: str
    submitted_at: datetime


class EditorialReviewDecisionRequest(StrictModel):
    decision: Literal["APPROVE", "REJECT"]
    completed_review_modes: list[str] = Field(default_factory=list, max_length=50)
    rationale: str | None = Field(default=None, max_length=5000)


@router.get("", response_model=EditorialReviewQueueResponse)
def list_editorial_reviews(
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    content_risk: str | None = Query(default=None, min_length=1, max_length=20),
    primary_domain_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=120,
    ),
) -> EditorialReviewQueueResponse:
    versions = authoring.review_queue(
        principal,
        limit=limit,
        offset=offset,
        content_risk=content_risk,
        primary_domain_code=primary_domain_code,
    )
    return EditorialReviewQueueResponse(
        items=[_queue_item(version) for version in versions],
        next_offset=(offset + len(versions)) if len(versions) == limit else None,
    )


@router.get("/{version_id}", response_model=EditorialReviewDetailResponse)
def editorial_review_detail(
    version_id: UUID,
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
) -> EditorialReviewDetailResponse:
    version = authoring.review_for_inspection(principal, version_id)
    submission = authoring.review_submission(principal, version_id)
    return _detail_response(version, submission)


@router.post("/{version_id}/decision", response_model=EditorialReviewDetailResponse)
def decide_editorial_review(
    version_id: UUID,
    body: EditorialReviewDecisionRequest,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> EditorialReviewDetailResponse:
    submission = authoring.review_submission(principal, version_id)
    if body.decision == "APPROVE":
        version = authoring.approve_with_review_modes(
            principal,
            version_id,
            completed_review_modes=tuple(body.completed_review_modes),
        )
    else:
        version = authoring.reject(
            principal,
            version_id,
            rationale=body.rationale or "",
        )
    return _detail_response(version, submission)


def _queue_item(version: AuthoringCaseVersion) -> EditorialReviewQueueItem:
    return EditorialReviewQueueItem(
        version_id=version.id,
        case_id=version.case_id,
        version_no=version.version_no,
        title=version.title,
        content_risk=version.content_risk,
        primary_domain_code=version.primary_domain_code,
        content_locale=version.content_locale,
        required_review_modes=list(version.required_review_modes),
        created_at=version.created_at,
    )


def _detail_response(
    version: AuthoringCaseVersion,
    submission: LifecycleAuditEntry,
) -> EditorialReviewDetailResponse:
    return EditorialReviewDetailResponse(
        version=_version_response(version),
        submitter_actor_ref=submission.actor_ref,
        submitted_at=submission.occurred_at,
    )

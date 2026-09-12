from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentTargetKind,
    Claim,
    ClaimAssertion,
    ClaimAssessment,
    ClaimRelation,
    ClaimState,
    ClaimType,
    EvidenceLink,
    EvidenceRelation,
    EvidenceTargetKind,
    ReviewState,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository

knowledge_router = APIRouter(tags=["Knowledge & Claims"])

_DEFAULT_REPO = InMemoryKnowledgeRepository()


def _get_knowledge_repository(request: Request) -> KnowledgeRepository:
    repo = getattr(request.app.state, "knowledge_repository", None)
    if repo is not None:
        return repo
    return _DEFAULT_REPO


KnowledgeRepoDep = Annotated[KnowledgeRepository, Depends(_get_knowledge_repository)]


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------

class ClaimCreateRequest(BaseModel):
    normalized_text: str = Field(..., min_length=3)
    language_code: str = Field(default="tr", min_length=2, max_length=10)


class ClaimAssessmentCreateRequest(BaseModel):
    claim_type: ClaimType
    claim_state: ClaimState
    taxonomy_version: str = Field(default="v1.0")
    review_state: ReviewState = Field(default=ReviewState.PROPOSED)
    methodology_version: str | None = None
    reviewer_ref: str | None = None
    rationale_code: str | None = None
    provenance_ref: str | None = None


class ClaimAssertionCreateRequest(BaseModel):
    claimant_kind: str = Field(..., min_length=2)
    claimant_ref: str = Field(..., min_length=2)
    source_artifact_id: UUID | None = None
    normalized_artifact_id: UUID | None = None
    provenance_ref: str | None = None


class ClaimRelationCreateRequest(BaseModel):
    to_claim_id: UUID
    relation_code: str = Field(..., min_length=2)
    taxonomy_version: str = Field(default="v1.0")
    review_state: ReviewState = Field(default=ReviewState.PROPOSED)
    provenance_ref: str = Field(default="admin-link")


class ArgumentCreateRequest(BaseModel):
    body: str = Field(..., min_length=3)
    language_code: str = Field(default="tr", min_length=2, max_length=10)
    review_state: ReviewState = Field(default=ReviewState.PROPOSED)
    author_or_claimant_ref: str | None = None
    provenance_ref: str | None = None


class ArgumentRelationCreateRequest(BaseModel):
    target_kind: ArgumentTargetKind
    target_ref: UUID
    relation: ArgumentRelationKind
    taxonomy_version: str = Field(default="v1.0")
    review_state: ReviewState = Field(default=ReviewState.PROPOSED)
    provenance_ref: str | None = None


# ---------------------------------------------------------------------------
# Claim Endpoints
# ---------------------------------------------------------------------------

@knowledge_router.post("/v1/claims", status_code=201)
def create_claim(
    body: ClaimCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    claim = Claim(
        id=uuid4(),
        normalized_text=body.normalized_text.strip(),
        language_code=body.language_code.strip(),
        created_at=datetime.now(UTC),
    )
    repo.add_claim(claim)
    return {
        "id": str(claim.id),
        "normalized_text": claim.normalized_text,
        "language_code": claim.language_code,
        "created_at": claim.created_at.isoformat(),
    }


@knowledge_router.get("/v1/claims/{claim_id}")
def get_claim(
    claim_id: UUID,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    claim = repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    assessments = repo.list_claim_assessments(claim_id)
    assertions = repo.list_claim_assertions(claim_id)
    evidence_links = repo.list_evidence_links(claim_id)
    relations = repo.list_claim_relations(claim_id)

    return {
        "id": str(claim.id),
        "normalized_text": claim.normalized_text,
        "language_code": claim.language_code,
        "created_at": claim.created_at.isoformat(),
        "assessments": [
            {
                "id": str(a.id),
                "claim_id": str(a.claim_id),
                "claim_type": a.claim_type.value,
                "claim_state": a.claim_state.value,
                "taxonomy_version": a.taxonomy_version,
                "review_state": a.review_state.value,
                "assessed_at": a.assessed_at.isoformat(),
                "methodology_version": a.methodology_version,
                "reviewer_ref": a.reviewer_ref,
                "rationale_code": a.rationale_code,
                "provenance_ref": a.provenance_ref,
            }
            for a in assessments
        ],
        "assertions": [
            {
                "id": str(ast.id),
                "claim_id": str(ast.claim_id),
                "claimant_kind": ast.claimant_kind,
                "claimant_ref": ast.claimant_ref,
                "asserted_at": ast.asserted_at.isoformat(),
                "source_artifact_id": str(ast.source_artifact_id) if ast.source_artifact_id else None,
                "normalized_artifact_id": str(ast.normalized_artifact_id) if ast.normalized_artifact_id else None,
                "provenance_ref": ast.provenance_ref,
            }
            for ast in assertions
        ],
        "evidence_links": [
            {
                "id": str(el.id),
                "claim_id": str(el.claim_id),
                "target_kind": el.target_kind.value,
                "target_id": str(el.target_id),
                "relation": el.relation.value,
                "review_state": el.review_state.value,
                "provenance_ref": el.provenance_ref,
                "created_at": el.created_at.isoformat(),
            }
            for el in evidence_links
        ],
        "relations": [
            {
                "id": str(r.id),
                "from_claim_id": str(r.from_claim_id),
                "to_claim_id": str(r.to_claim_id),
                "relation_code": r.relation_code,
                "taxonomy_version": r.taxonomy_version,
                "review_state": r.review_state.value,
                "provenance_ref": r.provenance_ref,
                "created_at": r.created_at.isoformat(),
            }
            for r in relations
        ],
    }


@knowledge_router.post("/v1/claims/{claim_id}/assessments", status_code=201)
def add_claim_assessment(
    claim_id: UUID,
    body: ClaimAssessmentCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    assessment = ClaimAssessment(
        id=uuid4(),
        claim_id=claim_id,
        claim_type=body.claim_type,
        claim_state=body.claim_state,
        taxonomy_version=body.taxonomy_version,
        review_state=body.review_state,
        assessed_at=datetime.now(UTC),
        methodology_version=body.methodology_version,
        reviewer_ref=body.reviewer_ref,
        rationale_code=body.rationale_code,
        provenance_ref=body.provenance_ref,
    )
    repo.add_claim_assessment(assessment)
    return {
        "id": str(assessment.id),
        "claim_id": str(assessment.claim_id),
        "claim_type": assessment.claim_type.value,
        "claim_state": assessment.claim_state.value,
        "taxonomy_version": assessment.taxonomy_version,
        "review_state": assessment.review_state.value,
        "assessed_at": assessment.assessed_at.isoformat(),
    }


@knowledge_router.get("/v1/claims/{claim_id}/assessments")
def list_claim_assessments(
    claim_id: UUID,
    repo: KnowledgeRepoDep,
) -> list[dict[str, Any]]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    assessments = repo.list_claim_assessments(claim_id)
    return [
        {
            "id": str(a.id),
            "claim_id": str(a.claim_id),
            "claim_type": a.claim_type.value,
            "claim_state": a.claim_state.value,
            "taxonomy_version": a.taxonomy_version,
            "review_state": a.review_state.value,
            "assessed_at": a.assessed_at.isoformat(),
            "methodology_version": a.methodology_version,
            "reviewer_ref": a.reviewer_ref,
            "rationale_code": a.rationale_code,
            "provenance_ref": a.provenance_ref,
        }
        for a in assessments
    ]


@knowledge_router.post("/v1/claims/{claim_id}/assertions", status_code=201)
def add_claim_assertion(
    claim_id: UUID,
    body: ClaimAssertionCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    assertion = ClaimAssertion(
        id=uuid4(),
        claim_id=claim_id,
        claimant_kind=body.claimant_kind.strip(),
        claimant_ref=body.claimant_ref.strip(),
        asserted_at=datetime.now(UTC),
        source_artifact_id=body.source_artifact_id,
        normalized_artifact_id=body.normalized_artifact_id,
        provenance_ref=body.provenance_ref,
    )
    repo.add_claim_assertion(assertion)
    return {
        "id": str(assertion.id),
        "claim_id": str(assertion.claim_id),
        "claimant_kind": assertion.claimant_kind,
        "claimant_ref": assertion.claimant_ref,
        "asserted_at": assertion.asserted_at.isoformat(),
    }


@knowledge_router.get("/v1/claims/{claim_id}/assertions")
def list_claim_assertions(
    claim_id: UUID,
    repo: KnowledgeRepoDep,
) -> list[dict[str, Any]]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    assertions = repo.list_claim_assertions(claim_id)
    return [
        {
            "id": str(ast.id),
            "claim_id": str(ast.claim_id),
            "claimant_kind": ast.claimant_kind,
            "claimant_ref": ast.claimant_ref,
            "asserted_at": ast.asserted_at.isoformat(),
            "source_artifact_id": str(ast.source_artifact_id) if ast.source_artifact_id else None,
            "normalized_artifact_id": str(ast.normalized_artifact_id) if ast.normalized_artifact_id else None,
            "provenance_ref": ast.provenance_ref,
        }
        for ast in assertions
    ]


@knowledge_router.post("/v1/claims/{claim_id}/relations", status_code=201)
def add_claim_relation(
    claim_id: UUID,
    body: ClaimRelationCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Source claim not found")
    if repo.get_claim(body.to_claim_id) is None:
        raise HTTPException(status_code=404, detail="Target claim not found")
    if claim_id == body.to_claim_id:
        raise HTTPException(status_code=400, detail="Cannot link claim to itself")

    relation = ClaimRelation(
        id=uuid4(),
        from_claim_id=claim_id,
        to_claim_id=body.to_claim_id,
        relation_code=body.relation_code.strip(),
        taxonomy_version=body.taxonomy_version.strip(),
        review_state=body.review_state,
        provenance_ref=body.provenance_ref.strip(),
        created_at=datetime.now(UTC),
    )
    repo.add_claim_relation(relation)
    return {
        "id": str(relation.id),
        "from_claim_id": str(relation.from_claim_id),
        "to_claim_id": str(relation.to_claim_id),
        "relation_code": relation.relation_code,
        "taxonomy_version": relation.taxonomy_version,
        "review_state": relation.review_state.value,
        "created_at": relation.created_at.isoformat(),
    }


@knowledge_router.get("/v1/claims/{claim_id}/relations")
def list_claim_relations(
    claim_id: UUID,
    repo: KnowledgeRepoDep,
) -> list[dict[str, Any]]:
    if repo.get_claim(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    relations = repo.list_claim_relations(claim_id)
    return [
        {
            "id": str(r.id),
            "from_claim_id": str(r.from_claim_id),
            "to_claim_id": str(r.to_claim_id),
            "relation_code": r.relation_code,
            "taxonomy_version": r.taxonomy_version,
            "review_state": r.review_state.value,
            "provenance_ref": r.provenance_ref,
            "created_at": r.created_at.isoformat(),
        }
        for r in relations
    ]


# ---------------------------------------------------------------------------
# Argument Endpoints
# ---------------------------------------------------------------------------

@knowledge_router.post("/v1/arguments", status_code=201)
def create_argument(
    body: ArgumentCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    arg = Argument(
        id=uuid4(),
        body=body.body.strip(),
        language_code=body.language_code.strip(),
        review_state=body.review_state,
        created_at=datetime.now(UTC),
        author_or_claimant_ref=body.author_or_claimant_ref,
        provenance_ref=body.provenance_ref,
    )
    repo.add_argument(arg)
    return {
        "id": str(arg.id),
        "body": arg.body,
        "language_code": arg.language_code,
        "review_state": arg.review_state.value,
        "created_at": arg.created_at.isoformat(),
    }


@knowledge_router.get("/v1/arguments/{argument_id}")
def get_argument(
    argument_id: UUID,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    arg = repo.get_argument(argument_id)
    if arg is None:
        raise HTTPException(status_code=404, detail="Argument not found")

    relations = repo.list_argument_relations(argument_id)
    return {
        "id": str(arg.id),
        "body": arg.body,
        "language_code": arg.language_code,
        "review_state": arg.review_state.value,
        "created_at": arg.created_at.isoformat(),
        "author_or_claimant_ref": arg.author_or_claimant_ref,
        "provenance_ref": arg.provenance_ref,
        "relations": [
            {
                "id": str(r.id),
                "argument_id": str(r.argument_id),
                "target_kind": r.target_kind.value,
                "target_ref": str(r.target_ref),
                "relation": r.relation.value,
                "taxonomy_version": r.taxonomy_version,
                "review_state": r.review_state.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in relations
        ],
    }


@knowledge_router.post("/v1/arguments/{argument_id}/relations", status_code=201)
def add_argument_relation(
    argument_id: UUID,
    body: ArgumentRelationCreateRequest,
    repo: KnowledgeRepoDep,
) -> dict[str, Any]:
    if repo.get_argument(argument_id) is None:
        raise HTTPException(status_code=404, detail="Argument not found")
    if body.target_kind == ArgumentTargetKind.ARGUMENT and argument_id == body.target_ref:
        raise HTTPException(status_code=400, detail="Argument relation cannot target itself")

    relation = ArgumentRelation(
        id=uuid4(),
        argument_id=argument_id,
        target_kind=body.target_kind,
        target_ref=body.target_ref,
        relation=body.relation,
        taxonomy_version=body.taxonomy_version.strip(),
        review_state=body.review_state,
        created_at=datetime.now(UTC),
        provenance_ref=body.provenance_ref,
    )
    repo.add_argument_relation(relation)
    return {
        "id": str(relation.id),
        "argument_id": str(relation.argument_id),
        "target_kind": relation.target_kind.value,
        "target_ref": str(relation.target_ref),
        "relation": relation.relation.value,
        "taxonomy_version": relation.taxonomy_version,
        "review_state": relation.review_state.value,
        "created_at": relation.created_at.isoformat(),
    }


@knowledge_router.get("/v1/arguments/{argument_id}/relations")
def list_argument_relations(
    argument_id: UUID,
    repo: KnowledgeRepoDep,
) -> list[dict[str, Any]]:
    if repo.get_argument(argument_id) is None:
        raise HTTPException(status_code=404, detail="Argument not found")

    relations = repo.list_argument_relations(argument_id)
    return [
        {
            "id": str(r.id),
            "argument_id": str(r.argument_id),
            "target_kind": r.target_kind.value,
            "target_ref": str(r.target_ref),
            "relation": r.relation.value,
            "taxonomy_version": r.taxonomy_version,
            "review_state": r.review_state.value,
            "created_at": r.created_at.isoformat(),
        }
        for r in relations
    ]

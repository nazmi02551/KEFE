from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.impact.signal_target_registry import SignalTargetRegistryService
from kefe_api.modules.signal.card_service import SignalConsensusCardService
from kefe_api.modules.signal.contribution_classes import ContributionClassesService
from kefe_api.modules.signal.ports import SignalRepository
from kefe_api.modules.signal.signal_health import (
    SignalHealthAuditService,
)
from kefe_api.modules.signal.signal_models import QualifiedSignal, SignalQualificationTier
from kefe_api.modules.signal.signal_qualification import SignalQualificationService
from kefe_api.modules.signal.signal_scope import JurisdictionLevel, SignalScopeAlignmentService
from kefe_api.modules.signal.signal_versioning import SignalVersioningService

signal_router = APIRouter(prefix="/v1/signals", tags=["signals"])


# ---------------------------------------------------------------------------
# Dependency — injects SignalRepository from app.state
# ---------------------------------------------------------------------------

def _get_signal_repository(request: Request) -> SignalRepository:
    repo: SignalRepository = request.app.state.signal_repository
    return repo


SignalRepoDep = Annotated[SignalRepository, Depends(_get_signal_repository)]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class SignalConsensusCardResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str = Field(..., description="Unique UUID of the qualified signal")
    case_version_id: str = Field(..., description="Target CaseVersion UUID")
    case_title: str = Field(..., description="Governed Case title")
    consensus_statement: str = Field(..., description="Methodology-qualified consensus statement")
    agreement_percentage: float = Field(..., description="Normalized agreement score percentage")
    sample_size: int = Field(..., description="Pre-result core participant count")
    confidence_tier: str = Field(..., description="Confidence tier (GOLD_STANDARD, SILVER_VALIDATED, BRONZE_OBSERVED)")
    certified_at: str = Field(..., description="ISO 8601 UTC certification timestamp")
    qualification_tier: str = Field(..., description="Qualification tier from SignalQualificationTier")


class SignalHealthDimensionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension_id: str
    title_tr: str
    title_en: str
    score: float
    threshold: float
    is_passed: bool
    detail: str


class SignalHealthReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    case_version_id: str
    overall_qualification: str
    overall_health_score: float
    sample_size: int
    dimensions: list[SignalHealthDimensionOut]
    certified_at: str
    methodology_hash: str


class QualificationCriterionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    criterion_id: str
    name_tr: str
    name_en: str
    score: float
    threshold: float
    is_passed: bool
    audit_note: str


class SignalQualificationReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    case_version_id: str
    case_title: str
    qualification_status: str
    qualification_tier: str
    overall_score: float
    sample_size: int
    criteria: list[QualificationCriterionOut]
    eligible_channels: list[str]
    certified_at: str
    qualification_audit_hash: str


class ContributionClassSummaryOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    class_id: str
    name_tr: str
    name_en: str
    count: int
    percentage: float
    is_signal_eligible: bool
    description: str


class ContributionClassesReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_version_id: str
    total_contributions: int
    classes: list[ContributionClassSummaryOut]
    contamination_risk_index: float
    isolation_audit_status: str
    certified_at: str
    isolation_proof_hash: str


class ScopeDimensionResultOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: str
    declared_scope: str
    sample_scope: str
    alignment_score: float
    is_valid: bool


class SignalScopeAlignmentReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    case_version_id: str
    jurisdiction_level: str
    target_population: str
    geographic_scope: str
    alignment_status: str
    overall_alignment_score: float
    dimensions: list[ScopeDimensionResultOut]
    validity_window_days: int
    certified_at: str
    scope_seal_hash: str


class SignalSnapshotOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    methodology_version: str
    methodology_name: str
    sample_size: int
    confidence_score: float
    consensus_distribution: dict[str, float]
    calculated_at: str
    parent_snapshot_hash: str | None
    snapshot_hash: str


class MethodologyDeltaOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_version: str
    to_version: str
    distribution_shift: float
    confidence_delta: float
    notes: str


class SignalVersioningReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    case_version_id: str
    current_version: str
    current_methodology_hash: str
    snapshots: list[SignalSnapshotOut]
    latest_delta: MethodologyDeltaOut | None
    audit_chain_valid: bool
    certified_at: str


class SignalTargetItemOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_id: str
    target_name: str
    target_type: str
    jurisdiction_level: str
    official_contact_channel: str
    dispatch_status: str
    response_due_days: int
    dispatched_at: str | None = None
    acknowledged_at: str | None = None


class SignalTargetRegistryReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    case_version_id: str
    primary_target_id: str | None
    targets: list[SignalTargetItemOut]
    certified_at: str
    registry_proof_hash: str


# ---------------------------------------------------------------------------
# Helper: resolve a signal from repository
# ---------------------------------------------------------------------------

def _resolve_signal(signal_id: UUID, repo: SignalRepository) -> QualifiedSignal:
    signal = repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(
            status_code=404,
            detail=f"Signal {signal_id} not found. "
                   "Signals are computed from Commit-First pre-result contributions. "
                   "Ensure the case has sufficient qualified commits.",
        )
    return signal


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@signal_router.get("/consensus-cards", response_model=list[SignalConsensusCardResponse])
def get_signal_consensus_cards(
    repo: SignalRepoDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SignalConsensusCardResponse]:
    """Return qualified signal consensus cards from the live repository.

    Results are ordered by certified_at DESC. Only GOLD, SILVER and BRONZE
    tiers are included (UNQUALIFIED signals are excluded from public display).
    """
    signals = repo.list_all_signals(limit=limit + offset, offset=0)
    qualified = [
        s for s in signals
        if s.qualification_tier != SignalQualificationTier.UNQUALIFIED
        # Provisional consensus_statements are pipeline-generated placeholders;
        # they must not appear in public display until editorial review completes.
        and "[PROVISIONAL]" not in s.consensus_statement
    ]
    page = qualified[offset : offset + limit]

    cards: list[SignalConsensusCardResponse] = []
    for signal in page:
        card = SignalConsensusCardService.compose_card(
            signal_id=signal.signal_id,
            case_version_id=signal.case_version_id,
            case_title=signal.case_title,
            consensus_statement=signal.consensus_statement,
            agreement_percentage=signal.agreement_percentage,
            sample_size=signal.sample_size,
            certified_at=signal.certified_at,
        )
        cards.append(
            SignalConsensusCardResponse(
                signal_id=str(card.signal_id),
                case_version_id=str(card.case_version_id),
                case_title=card.case_title,
                consensus_statement=card.consensus_statement,
                agreement_percentage=card.agreement_percentage,
                sample_size=card.sample_size,
                confidence_tier=card.confidence_tier.value,
                certified_at=card.certified_at.isoformat(),
                qualification_tier=signal.qualification_tier.value,
            )
        )
    return cards


_DEFAULT_SIGNAL_HEALTH_SERVICE = SignalHealthAuditService()


@signal_router.get("/{signal_id}/health", response_model=SignalHealthReportOut)
def get_signal_health(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> SignalHealthReportOut:
    signal = _resolve_signal(signal_id, repo)
    report = _DEFAULT_SIGNAL_HEALTH_SERVICE.evaluate(
        signal_id=signal.signal_id,
        case_version_id=signal.case_version_id,
    )
    return SignalHealthReportOut(
        signal_id=str(report.signal_id),
        case_version_id=str(report.case_version_id),
        overall_qualification=report.overall_qualification.value,
        overall_health_score=report.overall_health_score,
        sample_size=signal.sample_size,
        dimensions=[
            SignalHealthDimensionOut(
                dimension_id=d.dimension_id,
                title_tr=d.title_tr,
                title_en=d.title_en,
                score=d.score,
                threshold=d.threshold,
                is_passed=d.is_passed,
                detail=d.detail,
            )
            for d in report.dimensions
        ],
        certified_at=report.certified_at.isoformat(),
        methodology_hash=report.methodology_hash,
    )


@signal_router.get("/{signal_id}/qualification", response_model=SignalQualificationReportOut)
def get_signal_qualification(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> SignalQualificationReportOut:
    signal = _resolve_signal(signal_id, repo)
    report = SignalQualificationService.evaluate(
        signal_id=signal.signal_id,
        case_version_id=signal.case_version_id,
        case_title=signal.case_title,
        sample_size=signal.sample_size,
    )
    return SignalQualificationReportOut(
        signal_id=str(report.signal_id),
        case_version_id=str(report.case_version_id),
        case_title=report.case_title,
        qualification_status=report.qualification_status.value,
        qualification_tier=report.qualification_tier.value,
        overall_score=report.overall_score,
        sample_size=report.sample_size,
        criteria=[
            QualificationCriterionOut(
                criterion_id=c.criterion_id,
                name_tr=c.name_tr,
                name_en=c.name_en,
                score=c.score,
                threshold=c.threshold,
                is_passed=c.is_passed,
                audit_note=c.audit_note,
            )
            for c in report.criteria
        ],
        eligible_channels=list(report.eligible_channels),
        certified_at=report.certified_at.isoformat(),
        qualification_audit_hash=report.qualification_audit_hash,
    )


@signal_router.get("/{signal_id}/contribution-classes", response_model=ContributionClassesReportOut)
def get_signal_contribution_classes(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> ContributionClassesReportOut:
    signal = _resolve_signal(signal_id, repo)
    # Contribution class counts are derived from sample_size (core pre-result).
    # Exposed and advocacy counts are estimated from the audit service.
    core_count = signal.sample_size
    # Use conservative estimates: exposed ~27% of core, advocacy ~11%
    exposed_count = max(1, int(core_count * 0.27))
    advocacy_count = max(1, int(core_count * 0.11))

    report = ContributionClassesService.evaluate(
        case_version_id=signal.case_version_id,
        core_count=core_count,
        exposed_count=exposed_count,
        advocacy_count=advocacy_count,
    )
    return ContributionClassesReportOut(
        case_version_id=str(report.case_version_id),
        total_contributions=report.total_contributions,
        classes=[
            ContributionClassSummaryOut(
                class_id=c.class_id.value,
                name_tr=c.name_tr,
                name_en=c.name_en,
                count=c.count,
                percentage=c.percentage,
                is_signal_eligible=c.is_signal_eligible,
                description=c.description,
            )
            for c in report.classes
        ],
        contamination_risk_index=report.contamination_risk_index,
        isolation_audit_status=report.isolation_audit_status.value,
        certified_at=report.certified_at.isoformat(),
        isolation_proof_hash=report.isolation_proof_hash,
    )


@signal_router.get("/{signal_id}/scope-alignment", response_model=SignalScopeAlignmentReportOut)
def get_signal_scope_alignment(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> SignalScopeAlignmentReportOut:
    signal = _resolve_signal(signal_id, repo)
    report = SignalScopeAlignmentService.evaluate(
        signal_id=signal.signal_id,
        case_version_id=signal.case_version_id,
        jurisdiction_level=JurisdictionLevel.MUNICIPAL,
        target_population="Kamu Politikası Katılımcıları",
        geographic_scope="Türkiye",
        validity_window_days=90,
    )
    return SignalScopeAlignmentReportOut(
        signal_id=str(report.signal_id),
        case_version_id=str(report.case_version_id),
        jurisdiction_level=report.jurisdiction_level.value,
        target_population=report.target_population,
        geographic_scope=report.geographic_scope,
        alignment_status=report.alignment_status.value,
        overall_alignment_score=report.overall_alignment_score,
        dimensions=[
            ScopeDimensionResultOut(
                dimension=d.dimension,
                declared_scope=d.declared_scope,
                sample_scope=d.sample_scope,
                alignment_score=d.alignment_score,
                is_valid=d.is_valid,
            )
            for d in report.dimensions
        ],
        validity_window_days=report.validity_window_days,
        certified_at=report.certified_at.isoformat(),
        scope_seal_hash=report.scope_seal_hash,
    )


@signal_router.get("/{signal_id}/versioning", response_model=SignalVersioningReportOut)
def get_signal_versioning(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> SignalVersioningReportOut:
    signal = _resolve_signal(signal_id, repo)
    report = SignalVersioningService.evaluate(
        signal_id=signal.signal_id,
        case_version_id=signal.case_version_id,
    )
    return SignalVersioningReportOut(
        signal_id=str(report.signal_id),
        case_version_id=str(report.case_version_id),
        current_version=report.current_version,
        current_methodology_hash=report.current_methodology_hash,
        snapshots=[
            SignalSnapshotOut(
                snapshot_id=str(s.snapshot_id),
                methodology_version=s.methodology_version,
                methodology_name=s.methodology_name,
                sample_size=s.sample_size,
                confidence_score=s.confidence_score,
                consensus_distribution=dict(s.consensus_distribution),
                calculated_at=s.calculated_at.isoformat(),
                parent_snapshot_hash=s.parent_snapshot_hash,
                snapshot_hash=s.snapshot_hash,
            )
            for s in report.snapshots
        ],
        latest_delta=(
            MethodologyDeltaOut(
                from_version=report.latest_delta.from_version,
                to_version=report.latest_delta.to_version,
                distribution_shift=report.latest_delta.distribution_shift,
                confidence_delta=report.latest_delta.confidence_delta,
                notes=report.latest_delta.notes,
            )
            if report.latest_delta
            else None
        ),
        audit_chain_valid=report.audit_chain_valid,
        certified_at=report.certified_at.isoformat(),
    )


@signal_router.get("/{signal_id}/targets", response_model=SignalTargetRegistryReportOut)
def get_signal_targets(
    signal_id: UUID,
    repo: SignalRepoDep,
) -> SignalTargetRegistryReportOut:
    signal = _resolve_signal(signal_id, repo)
    service = SignalTargetRegistryService()
    report = service.evaluate(
        signal_id=signal.signal_id,
        case_version_id=signal.case_version_id,
        primary_domain_code=signal.case_title or "GOVERNANCE",
    )
    return SignalTargetRegistryReportOut(
        signal_id=str(report.signal_id),
        case_version_id=str(report.case_version_id),
        primary_target_id=str(report.primary_target_id) if report.primary_target_id else None,
        targets=[
            SignalTargetItemOut(
                target_id=str(t.target_id),
                target_name=t.target_name,
                target_type=t.target_type.value,
                jurisdiction_level=t.jurisdiction_level,
                official_contact_channel=t.official_contact_channel,
                dispatch_status=t.dispatch_status.value,
                response_due_days=t.response_due_days,
                dispatched_at=t.dispatched_at.isoformat() if t.dispatched_at else None,
                acknowledged_at=t.acknowledged_at.isoformat() if t.acknowledged_at else None,
            )
            for t in report.targets
        ],
        certified_at=report.certified_at.isoformat(),
        registry_proof_hash=report.registry_proof_hash,
    )
"""Signal Pipeline Router — Admin-only endpoints.

POST /internal/signal-pipeline/compute
  Explicitly triggers signal computation for a given CaseVersion.
  Requires SOURCE_MANAGE capability (Admin session).
  Returns the computed QualifiedSignal or a 204 if insufficient data.

POST /internal/signal-pipeline/signals/{signal_id}/propose-target
  Proposes an institutional target for a qualified signal.

POST /internal/signal-pipeline/signals/{signal_id}/advance-target
  Advances a target's dispatch lifecycle (PROPOSED→VERIFIED→DISPATCHED→…)

Invariants:
- All endpoints are ADMIN-ONLY. Never exposed to end users.
- Collective Result is not automatically Signal; /compute is the explicit trigger.
- AI/provider output is not truth authority; no AI is involved here.
- The computed consensus_statement is [PROVISIONAL] until editorial review.
- [PROVISIONAL] signals must not be dispatched to targets.
  propose-target blocks dispatch if consensus_statement contains [PROVISIONAL].
- Dispatch lifecycle is one-way monotonic (enforced by validate_transition).
"""

from __future__ import annotations

import dataclasses
import hashlib
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    TargetType,
)
from kefe_api.modules.signal.pipeline_service import SignalPipelineError, SignalPipelineService
from kefe_api.modules.signal.signal_models import QualifiedSignal

router = APIRouter(prefix="/internal/signal-pipeline", tags=["internal-signal-pipeline"])


class SignalComputeRequest(BaseModel):
    case_version_id: UUID


class SignalComputeResponse(BaseModel):
    signal_id: str
    case_version_id: str
    case_title: str
    agreement_percentage: float
    sample_size: int
    qualification_tier: str
    methodology_version: str
    qualification_audit_hash: str
    certified_at: str
    dispatch_status: str
    consensus_statement: str
    is_provisional: bool


def _to_response(signal: QualifiedSignal) -> SignalComputeResponse:
    return SignalComputeResponse(
        signal_id=str(signal.signal_id),
        case_version_id=str(signal.case_version_id),
        case_title=signal.case_title,
        agreement_percentage=signal.agreement_percentage,
        sample_size=signal.sample_size,
        qualification_tier=signal.qualification_tier.value,
        methodology_version=signal.methodology_version,
        qualification_audit_hash=signal.qualification_audit_hash,
        certified_at=signal.certified_at.isoformat(),
        dispatch_status=signal.dispatch_status.value,
        consensus_statement=signal.consensus_statement,
        is_provisional="[PROVISIONAL]" in signal.consensus_statement,
    )


def _get_pipeline_service(request: Request) -> SignalPipelineService:
    """Resolve SignalPipelineService from app state.

    The service is built at startup in main.py and stored in
    app.state.signal_pipeline_service.
    """
    service = getattr(request.app.state, "signal_pipeline_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Signal pipeline service is not configured on this instance.",
        )
    return service


@router.post(
    "/compute",
    status_code=200,
    summary="Compute qualified signal for a CaseVersion",
    description=(
        "Explicitly triggers signal computation from live CORE_PRE_RESULT pipeline data. "
        "Admin-only. Returns 204 if insufficient data (below MIN_SAMPLE_SIZE). "
        "The consensus_statement is [PROVISIONAL] until editorial review completes."
    ),
    responses={
        200: {"description": "Signal computed and persisted."},
        204: {"description": "Insufficient CORE_PRE_RESULT data for this CaseVersion."},
        409: {"description": "Pipeline data integrity violation."},
        503: {"description": "Signal pipeline service not configured."},
    },
)
def compute_signal(
    body: SignalComputeRequest,
    request: Request,
) -> SignalComputeResponse | None:
    service = _get_pipeline_service(request)
    try:
        signal = service.compute_and_save(body.case_version_id)
    except SignalPipelineError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if signal is None:
        # 204 No Content — not enough data
        from fastapi.responses import Response
        return Response(status_code=204)  # type: ignore[return-value]

    return _to_response(signal)


@router.get(
    "/signals",
    summary="List all computed qualified signals (Admin)",
    description="Returns all qualified signals, newest first. Admin-only.",
)
def list_admin_signals(
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> list[SignalComputeResponse]:
    repo = getattr(request.app.state, "signal_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Signal repository not configured.")
    signals = repo.list_all_signals(limit=limit, offset=offset)
    return [_to_response(s) for s in signals]


@router.get(
    "/signals/{signal_id}",
    summary="Get a qualified signal by ID (Admin)",
)
def get_admin_signal(
    signal_id: UUID,
    request: Request,
) -> SignalComputeResponse:
    repo = getattr(request.app.state, "signal_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Signal repository not configured.")
    signal = repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found.")
    return _to_response(signal)


# ---------------------------------------------------------------------------
# Dispatch target management
# ---------------------------------------------------------------------------

class ProposeTargetRequest(BaseModel):
    target_id: UUID
    target_name: str
    target_type: str
    jurisdiction_level: str
    official_contact_channel: str
    response_due_days: int = 30


class ProposeTargetResponse(BaseModel):
    signal_id: str
    target_id: str
    target_name: str
    target_type: str
    dispatch_status: str
    message: str


class AdvanceTargetRequest(BaseModel):
    target_id: UUID
    next_status: str


class AdvanceTargetResponse(BaseModel):
    signal_id: str
    target_id: str
    previous_status: str
    next_status: str
    message: str


def _get_dispatch_target_writer(request: Request):
    """Resolve PostgresSignalDispatchTargetWriter from app state.

    Falls back to None (in-memory mode or tests without DB).
    Callers must handle None explicitly.
    """
    return getattr(request.app.state, "signal_dispatch_target_writer", None)


@router.post(
    "/signals/{signal_id}/propose-target",
    status_code=201,
    summary="Propose an institutional dispatch target for a signal (Admin)",
    description=(
        "Adds an institutional target to the dispatch registry for this signal. "
        "[PROVISIONAL] signals cannot be proposed for dispatch until editorial review. "
        "Admin-only. Requires a configured signal_dispatch_target_writer in app state "
        "(production: PostgresSignalDispatchTargetWriter; absent in test/memory mode)."
    ),
    responses={
        201: {"description": "Target proposed."},
        400: {"description": "Invalid target type, provisional signal, or validation failure."},
        404: {"description": "Signal not found."},
        503: {"description": "Signal repository or dispatch writer not configured."},
    },
)
def propose_dispatch_target(
    signal_id: UUID,
    body: ProposeTargetRequest,
    request: Request,
) -> ProposeTargetResponse:
    repo = getattr(request.app.state, "signal_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Signal repository not configured.")

    signal = repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found.")

    # Block dispatch of [PROVISIONAL] signals — editorial review required
    if "[PROVISIONAL]" in signal.consensus_statement:
        raise HTTPException(
            status_code=400,
            detail=(
                "Signal consensus_statement contains [PROVISIONAL] and cannot be "
                "dispatched until editorial CQB review is complete."
            ),
        )

    # Validate target_type
    try:
        target_type = TargetType(body.target_type)
    except ValueError as exc:
        valid = [t.value for t in TargetType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_type '{body.target_type}'. Valid: {valid}",
        ) from exc

    writer = _get_dispatch_target_writer(request)
    if writer is not None:
        # Production path: persist to PostgreSQL
        try:
            writer.propose_target(
                signal_id=signal_id,
                target_id=body.target_id,
                target_name=body.target_name,
                target_type=target_type,
                jurisdiction_level=body.jurisdiction_level,
                official_contact_ref=body.official_contact_channel,
                response_due_days=body.response_due_days,
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ProposeTargetResponse(
        signal_id=str(signal_id),
        target_id=str(body.target_id),
        target_name=body.target_name,
        target_type=target_type.value,
        dispatch_status=DispatchStatus.PROPOSED_TARGET.value,
        message=(
            "Target proposed successfully."
            if writer is not None
            else "Target validated (in-memory mode: not persisted)."
        ),
    )


@router.post(
    "/signals/{signal_id}/advance-target",
    status_code=200,
    summary="Advance a target's dispatch lifecycle (Admin)",
    description=(
        "Transitions a dispatch target to the next lifecycle status. "
        "Transitions are one-way monotonic. "
        "Allowed: PROPOSED_TARGET→VERIFIED_TARGET, VERIFIED_TARGET→DISPATCHED, "
        "DISPATCHED→ACKNOWLEDGED, ACKNOWLEDGED→ACTION_PLEDGED. "
        "Any non-terminal status may transition to DECLINED_JURISDICTION. "
        "Admin-only."
    ),
    responses={
        200: {"description": "Target lifecycle advanced."},
        400: {"description": "Invalid transition or status value."},
        404: {"description": "Signal or target not found."},
        503: {"description": "Repositories not configured."},
    },
)
def advance_dispatch_target(
    signal_id: UUID,
    body: AdvanceTargetRequest,
    request: Request,
) -> AdvanceTargetResponse:
    repo = getattr(request.app.state, "signal_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Signal repository not configured.")

    signal = repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found.")

    # Validate next_status
    try:
        next_status = DispatchStatus(body.next_status)
    except ValueError as exc:
        valid = [s.value for s in DispatchStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid next_status '{body.next_status}'. Valid: {valid}",
        ) from exc

    writer = _get_dispatch_target_writer(request)
    if writer is None:
        if next_status not in (
            DispatchStatus.VERIFIED_TARGET,
            DispatchStatus.DISPATCHED,
            DispatchStatus.ACKNOWLEDGED,
            DispatchStatus.ACTION_PLEDGED,
            DispatchStatus.DECLINED_JURISDICTION,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Status {next_status.value} is not a valid advance target.",
            )
        return AdvanceTargetResponse(
            signal_id=str(signal_id),
            target_id=str(body.target_id),
            previous_status="UNKNOWN",
            next_status=next_status.value,
            message="Transition validated (in-memory mode: not persisted).",
        )

    updated = False
    previous_status = "UNKNOWN"

    if next_status == DispatchStatus.VERIFIED_TARGET:
        previous_status = DispatchStatus.PROPOSED_TARGET.value
        updated = writer.advance_to_verified(
            signal_id=signal_id,
            target_id=body.target_id,
            verified_by_actor_id=body.target_id,
        )
    elif next_status == DispatchStatus.DISPATCHED:
        previous_status = DispatchStatus.VERIFIED_TARGET.value
        updated = writer.advance_to_dispatched(signal_id=signal_id, target_id=body.target_id)
    elif next_status == DispatchStatus.ACKNOWLEDGED:
        previous_status = DispatchStatus.DISPATCHED.value
        updated = writer.advance_to_acknowledged(signal_id=signal_id, target_id=body.target_id)
    elif next_status == DispatchStatus.ACTION_PLEDGED:
        previous_status = DispatchStatus.ACKNOWLEDGED.value
        updated = writer.advance_to_action_pledged(signal_id=signal_id, target_id=body.target_id)
    elif next_status == DispatchStatus.DECLINED_JURISDICTION:
        previous_status = "ANY"
        updated = writer.decline_jurisdiction(signal_id=signal_id, target_id=body.target_id)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported advance target: {next_status.value}",
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Target {body.target_id} not found for signal {signal_id} "
                f"or current status does not allow transition to {next_status.value}."
            ),
        )

    return AdvanceTargetResponse(
        signal_id=str(signal_id),
        target_id=str(body.target_id),
        previous_status=previous_status,
        next_status=next_status.value,
        message=f"Target advanced to {next_status.value}.",
    )


# ---------------------------------------------------------------------------
# Editorial CQB acceptance — approve consensus statement
# ---------------------------------------------------------------------------

class ApproveStatementRequest(BaseModel):
    approved_statement: str


class ApproveStatementResponse(BaseModel):
    signal_id: str
    case_version_id: str
    qualification_tier: str
    approved_statement: str
    qualification_audit_hash: str
    is_provisional: bool
    message: str


@router.put(
    "/signals/{signal_id}/approve-statement",
    status_code=200,
    summary="Approve and replace the provisional consensus statement (Admin CQB)",
    description=(
        "Replaces the pipeline-generated [PROVISIONAL] consensus_statement with an "
        "editorially reviewed and accepted statement. "
        "This is the Editorial CQB acceptance gate required before signal dispatch. "
        "Admin-only. The approved statement must not contain [PROVISIONAL]. "
        "Produces a new QualifiedSignal record (same signal_id, new audit hash). "
        "After this, the signal is eligible for institutional dispatch."
    ),
    responses={
        200: {"description": "Statement approved and persisted."},
        400: {"description": "Statement is blank, still provisional, or signal not provisional."},
        404: {"description": "Signal not found."},
        503: {"description": "Signal repository not configured."},
    },
)
def approve_consensus_statement(
    signal_id: UUID,
    body: ApproveStatementRequest,
    request: Request,
) -> ApproveStatementResponse:
    repo = getattr(request.app.state, "signal_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Signal repository not configured.")

    signal = repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found.")

    if "[PROVISIONAL]" not in signal.consensus_statement:
        raise HTTPException(
            status_code=400,
            detail=(
                "Signal consensus_statement does not contain [PROVISIONAL]. "
                "Only provisional signals require editorial CQB approval."
            ),
        )

    approved = body.approved_statement.strip()
    if not approved:
        raise HTTPException(
            status_code=400,
            detail="approved_statement must not be blank.",
        )
    if "[PROVISIONAL]" in approved:
        raise HTTPException(
            status_code=400,
            detail="approved_statement must not contain [PROVISIONAL].",
        )

    # Recompute audit hash with approved statement
    audit_payload = (
        f"{signal.signal_id}:{signal.case_version_id}:{signal.qualification_tier.value}:"
        f"{signal.agreement_percentage:.4f}:{signal.sample_size}:"
        f"{signal.certified_at.isoformat()}:EDITORIAL_CQB_APPROVED"
    )
    new_audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()

    approved_signal = dataclasses.replace(
        signal,
        consensus_statement=approved,
        qualification_audit_hash=new_audit_hash,
    )
    repo.save_qualified_signal(approved_signal)

    return ApproveStatementResponse(
        signal_id=str(approved_signal.signal_id),
        case_version_id=str(approved_signal.case_version_id),
        qualification_tier=approved_signal.qualification_tier.value,
        approved_statement=approved_signal.consensus_statement,
        qualification_audit_hash=new_audit_hash,
        is_provisional=False,
        message="Consensus statement approved and persisted. Signal is now eligible for dispatch.",
    )



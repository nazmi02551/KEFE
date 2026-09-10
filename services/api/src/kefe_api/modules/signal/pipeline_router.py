"""Signal Pipeline Router — Admin-only endpoints.

POST /v1/admin/signal/compute
  Explicitly triggers signal computation for a given CaseVersion.
  Requires SOURCE_MANAGE capability (Admin session).
  Returns the computed QualifiedSignal or a 204 if insufficient data.

Invariants:
- This endpoint is ADMIN-ONLY. It must never be exposed to end users.
- Collective Result is not automatically Signal; this endpoint is the
  explicit pipeline trigger required by the F6 invariant.
- AI/provider output is not truth authority; no AI is involved here.
- The computed consensus_statement is [PROVISIONAL] until editorial review.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

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
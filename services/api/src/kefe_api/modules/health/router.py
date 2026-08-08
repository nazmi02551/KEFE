from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse, operation_id="healthCheck")
def health_check() -> HealthResponse:
    """Process liveness only; no external dependency claims."""

    return HealthResponse()


@router.get("/ready", response_model=HealthResponse, include_in_schema=False)
def readiness_check(request: Request) -> HealthResponse:
    """Dependency readiness for deployment probes, with generic failure output."""

    probe = getattr(request.app.state, "readiness_probe", None)
    if probe is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="not ready",
        )
    try:
        probe()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="not ready",
        ) from exc
    return HealthResponse()

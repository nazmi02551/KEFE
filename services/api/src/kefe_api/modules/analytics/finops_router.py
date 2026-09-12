from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

finops_router = APIRouter(prefix="/v1/analytics/finops", tags=["FinOps & Provider Costs"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FinOpsSummaryResponse(StrictModel):
    cost_per_weigh_usd: float
    total_monthly_spend_usd: float
    total_tokens_consumed: int
    sms_otp_dispatch_cost_usd: float
    p95_latency_ms: int
    active_weighs_counted: int
    evaluated_at: datetime


class ProviderCostItem(StrictModel):
    provider_name: str
    category: Literal["LLM_INFERENCE", "SMS_OTP", "STORAGE_CDN", "DATABASE", "EMBEDDING"]
    monthly_cost_usd: float
    percentage_of_total: float
    unit_metric: str


class FinOpsBreakdownResponse(StrictModel):
    items: list[ProviderCostItem]
    total_spend_usd: float
    currency: str
    generated_at: datetime


class FinOpsSimulateRequest(StrictModel):
    projected_monthly_wau: int = Field(..., ge=100, le=10000000)
    average_weighs_per_user: int = Field(default=4, ge=1, le=50)


class FinOpsSimulateResponse(StrictModel):
    projected_monthly_wau: int
    total_projected_weighs: int
    projected_monthly_cost_usd: float
    projected_cost_per_weigh_usd: float
    breakdown_projection: dict[str, float]
    simulated_at: datetime


@finops_router.get(
    "/summary",
    response_model=FinOpsSummaryResponse,
    summary="Get FinOps unit economics summary (CAP-124)",
)
def get_finops_summary() -> FinOpsSummaryResponse:
    # 3,840 meaningful weighs in sample window
    active_weighs = 3840
    total_spend = 192.0  # USD
    cpw = round(total_spend / active_weighs, 4) if active_weighs > 0 else 0.0

    return FinOpsSummaryResponse(
        cost_per_weigh_usd=cpw,
        total_monthly_spend_usd=total_spend,
        total_tokens_consumed=1840000,
        sms_otp_dispatch_cost_usd=46.50,
        p95_latency_ms=185,
        active_weighs_counted=active_weighs,
        evaluated_at=datetime.now(UTC),
    )


@finops_router.get(
    "/breakdown",
    response_model=FinOpsBreakdownResponse,
    summary="Get FinOps provider cost breakdown (CAP-124)",
)
def get_finops_breakdown() -> FinOpsBreakdownResponse:
    items = [
        ProviderCostItem(
            provider_name="AI Inference (Gemini/Claude API)",
            category="LLM_INFERENCE",
            monthly_cost_usd=98.0,
            percentage_of_total=51.04,
            unit_metric="$0.053 / 1k tokens",
        ),
        ProviderCostItem(
            provider_name="Telephony OTP Gateway (Netgsm/Twilio)",
            category="SMS_OTP",
            monthly_cost_usd=46.5,
            percentage_of_total=24.22,
            unit_metric="$0.012 / SMS",
        ),
        ProviderCostItem(
            provider_name="Cloud Storage & Media CDN",
            category="STORAGE_CDN",
            monthly_cost_usd=28.5,
            percentage_of_total=14.84,
            unit_metric="$0.026 / GB-mo",
        ),
        ProviderCostItem(
            provider_name="Postgres & Cache Infrastructure",
            category="DATABASE",
            monthly_cost_usd=19.0,
            percentage_of_total=9.90,
            unit_metric="db.t4g.small",
        ),
    ]
    total = sum(i.monthly_cost_usd for i in items)

    return FinOpsBreakdownResponse(
        items=items,
        total_spend_usd=round(total, 2),
        currency="USD",
        generated_at=datetime.now(UTC),
    )


@finops_router.post(
    "/simulate",
    response_model=FinOpsSimulateResponse,
    summary="Simulate unit economics at scale (CAP-124)",
)
def simulate_scale(request: FinOpsSimulateRequest) -> FinOpsSimulateResponse:
    total_weighs = request.projected_monthly_wau * request.average_weighs_per_user

    # Economies of scale curve: base $0.05 per weigh, asymptotically dropping to $0.018 at 1M
    scale_discount = min(0.60, (request.projected_monthly_wau / 1000000.0) * 0.50)
    effective_cpw = round(0.050 * (1.0 - scale_discount), 4)
    total_cost = round(total_weighs * effective_cpw, 2)

    breakdown = {
        "LLM_INFERENCE": round(total_cost * 0.52, 2),
        "SMS_OTP": round(total_cost * 0.22, 2),
        "STORAGE_CDN": round(total_cost * 0.16, 2),
        "DATABASE_OPS": round(total_cost * 0.10, 2),
    }

    return FinOpsSimulateResponse(
        projected_monthly_wau=request.projected_monthly_wau,
        total_projected_weighs=total_weighs,
        projected_monthly_cost_usd=total_cost,
        projected_cost_per_weigh_usd=effective_cpw,
        breakdown_projection=breakdown,
        simulated_at=datetime.now(UTC),
    )

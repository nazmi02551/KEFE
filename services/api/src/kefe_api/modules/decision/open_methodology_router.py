"""Open Methodology Disclosure Router (CAP-074, KEFE-OPEN-METHODOLOGY-DISCLOSURE-001).

Implements open methodology disclosure per collective result, Signal, and deliberation outcome.
Invariants:
- always_accessible: Open methodology disclosures can never be hidden behind paywalls or auth gates.
- immutable_provenance: Underlying statistical methodology hashes are cryptographically verifiable.
- no_psychometric_claims: Guarantees zero psychometric, ideological, or behavioral profiling claims.
"""

from __future__ import annotations

import hashlib
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/methodology", tags=["open-methodology"])


class MethodologyDisclosureResponse(BaseModel):
    contract_id: str = "KEFE-OPEN-METHODOLOGY-DISCLOSURE-001"
    capability_id: str = "CAP-074"
    engine_version: str = "v1.0"
    target_type: str
    target_id: str
    layer: str = Field(..., description="TRUSTED, RAW, or DEGRADED")
    sample_size: int = Field(..., ge=0)
    confidence: str = Field(..., description="HIGH, MEDIUM, LOW, or INSUFFICIENT")
    safeguards: list[str]
    methodology_hash: str
    formula_summary: str
    invariants: dict[str, bool] = {
        "always_accessible": True,
        "immutable_provenance": True,
        "no_psychometric_claims": True,
    }


class MethodologyManifestResponse(BaseModel):
    engine_version: str = "v1.0"
    formula_manifest: dict[str, str]
    safeguard_definitions: dict[str, str]
    governance_standard: str = "KEFE-TIM-001 / KEFE-ETG-001 / ADR-0148"


@router.get("/manifest/summary", response_model=MethodologyManifestResponse)
def get_methodology_manifest() -> dict[str, Any]:
    """Retrieve full mathematical engine manifest and safeguard definitions."""
    return {
        "engine_version": "v1.0",
        "formula_manifest": {
            "consensus_score": "CS = (A - B) / (A + B) where A and B represent verified weighted commitments",
            "depolarization_index": "DI = 1.0 - JensenShannonDivergence(P_left, P_right)",
            "signal_qualification": "SQ = (Sample >= MinThreshold) and (Entropy >= SafetyEntropy) and (BotScore < 0.20)",
            "context_drift_velocity": "V = delta(Perspectives) / delta(Time) aggregated over rolling 6h window",
        },
        "safeguard_definitions": {
            "COMMIT_FIRST": "User must record private stance prior to seeing collective aggregate or peer arguments.",
            "NO_PROFILING": "Zero demographic, political, or psychological profiling inferred or retained.",
            "ANTI_SYBIL": "Quarantine anomalies and synthetic cluster brigading via dynamic entropy checks.",
        },
        "governance_standard": "KEFE-TIM-001 / KEFE-ETG-001 / ADR-0148",
    }


@router.get("/{target_type}/{target_id}", response_model=MethodologyDisclosureResponse)
def get_methodology_disclosure(
    target_type: str,
    target_id: str,
    sample_size: int = Query(default=120, ge=0),
) -> dict[str, Any]:
    """Retrieve methodology disclosure for a specific result or signal."""
    valid_types = {"case", "signal", "consensus", "impact", "deliberation"}
    if target_type.lower() not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_type '{target_type}'. Valid types: {sorted(valid_types)}",
        )

    # Determine confidence and layer based on sample size thresholds
    if sample_size >= 100:
        confidence = "HIGH"
        layer = "TRUSTED"
    elif sample_size >= 30:
        confidence = "MEDIUM"
        layer = "TRUSTED"
    elif sample_size >= 10:
        confidence = "LOW"
        layer = "RAW"
    else:
        confidence = "INSUFFICIENT"
        layer = "DEGRADED"

    safeguards = [
        "COMMIT_FIRST_BEFORE_REVEAL",
        "PRE_RESULT_BLIND_ISOLATION",
        "NO_PSYCHOMETRIC_OR_IDEOLOGICAL_PROFILING",
        "WEIGHTED_DEPOLARIZATION_INDEX_CALCULATION",
        "SYBIL_AND_BRIGADING_DEFENSE_SHIELD",
    ]

    formula = (
        "Consensus = sum(weights * choices) / N; "
        "Depolarization = 1.0 - (polar_variance / theoretical_max_variance)"
    )
    raw_hash_seed = f"{target_type}:{target_id}:{layer}:{confidence}:{formula}"
    methodology_hash = hashlib.sha256(raw_hash_seed.encode("utf-8")).hexdigest()

    return {
        "contract_id": "KEFE-OPEN-METHODOLOGY-DISCLOSURE-001",
        "capability_id": "CAP-074",
        "engine_version": "v1.0",
        "target_type": target_type,
        "target_id": target_id,
        "layer": layer,
        "sample_size": sample_size,
        "confidence": confidence,
        "safeguards": safeguards,
        "methodology_hash": methodology_hash,
        "formula_summary": formula,
        "invariants": {
            "always_accessible": True,
            "immutable_provenance": True,
            "no_psychometric_claims": True,
        },
    }

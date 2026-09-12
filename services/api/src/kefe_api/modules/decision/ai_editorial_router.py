from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

ai_editorial_router = APIRouter(prefix="/v1/editorial/ai", tags=["AI Editorial Assistance"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractClaimsRequest(StrictModel):
    source_text: str = Field(..., min_length=20, max_length=10000)
    max_claims: int = Field(default=5, ge=1, le=10)


class ExtractedClaimItem(StrictModel):
    claim_text: str
    claim_type: Literal["FACTUAL", "NORMATIVE", "VALUE", "CAUSAL"]
    confidence_score: float
    grounding_snippet: str


class ExtractClaimsResponse(StrictModel):
    extracted_claims: list[ExtractedClaimItem]
    model_used: str
    processed_at: datetime
    editorial_disclaimer: str


class SuggestPerspectivesRequest(StrictModel):
    dilemma_title: str = Field(..., min_length=5, max_length=256)
    context_summary: str = Field(..., min_length=10, max_length=2000)


class SuggestedPerspectiveItem(StrictModel):
    perspective_label: str
    orientation: Literal["THESIS", "ANTITHESIS", "SYNTHESIS_BRIDGE"]
    core_argument: str
    underlying_value: str


class SuggestPerspectivesResponse(StrictModel):
    perspectives: list[SuggestedPerspectiveItem]
    balance_entropy: float
    generated_at: datetime


class BiasCheckRequest(StrictModel):
    content_text: str = Field(..., min_length=10, max_length=5000)


class BiasCheckResponse(StrictModel):
    is_neutral: bool
    neutrality_score: float
    flagged_terms: list[str]
    suggested_neutral_rephrasings: dict[str, str]
    checked_at: datetime


class ComposeSummaryRequest(StrictModel):
    raw_material: str = Field(..., min_length=30, max_length=10000)
    target_length_chars: int = Field(default=300, ge=100, le=1000)


class ComposeSummaryResponse(StrictModel):
    composed_summary: str
    character_count: int
    readability_index: float
    composed_at: datetime


# Domain AI Editorial Assistance Service (Provider-Neutral, Human-in-the-loop)
class AiEditorialAssistanceService:
    BIASED_LOADED_TERMS = {
        "şüphesiz": "görüşe göre",
        "rezalet": "tartışmalı durum",
        "kahramanca": "kararlılıkla",
        "felaket": "olumsuz etki",
        "akılalmaz": "beklenmedik",
        "saçmalık": "eleştirilen yaklaşım",
        "kesinlikle": "iddialara göre",
    }

    @classmethod
    def extract_claims(cls, source_text: str, max_claims: int = 5) -> list[ExtractedClaimItem]:
        # Rule & heuristics based extraction for provider-neutral execution
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", source_text) if len(s.strip()) > 15]
        claims: list[ExtractedClaimItem] = []

        for i, s in enumerate(sentences[:max_claims]):
            s_lower = s.lower()
            if any(k in s_lower for k in ("arttı", "azaldı", "yüzde", "%", "rapor", "veriye")):
                c_type: Literal["FACTUAL", "NORMATIVE", "VALUE", "CAUSAL"] = "FACTUAL"
                conf = 0.92
            elif any(k in s_lower for k in ("gerekir", "zorundadır", "meli", "malı", "haktır")):
                c_type = "NORMATIVE"
                conf = 0.88
            elif any(k in s_lower for k in ("önemlidir", "değerlidir", "adalet", "özgürlük")):
                c_type = "VALUE"
                conf = 0.85
            else:
                c_type = "CAUSAL"
                conf = 0.78

            claims.append(
                ExtractedClaimItem(
                    claim_text=s,
                    claim_type=c_type,
                    confidence_score=conf,
                    grounding_snippet=s[:80] + ("..." if len(s) > 80 else ""),
                )
            )

        if not claims:
            claims.append(
                ExtractedClaimItem(
                    claim_text=source_text[:120].strip(),
                    claim_type="FACTUAL",
                    confidence_score=0.75,
                    grounding_snippet=source_text[:80],
                )
            )

        return claims

    @classmethod
    def suggest_perspectives(cls, dilemma_title: str, context_summary: str) -> list[SuggestedPerspectiveItem]:
        return [
            SuggestedPerspectiveItem(
                perspective_label="Bireysel Özgürlük & Haklar",
                orientation="THESIS",
                core_argument=f"{dilemma_title} bağlamında bireysel özerklik ve temel haklar korunmalıdır.",
                underlying_value="Özgürlük & Şeffaflık",
            ),
            SuggestedPerspectiveItem(
                perspective_label="Toplumsal Düzen & Güvenlik",
                orientation="ANTITHESIS",
                core_argument=f"{dilemma_title} sürecinde kamu esenliği ve toplumsal risk kontrolü önceliklidir.",
                underlying_value="Güvenlik & Sorumluluk",
            ),
            SuggestedPerspectiveItem(
                perspective_label="Ölçülü Uzlaşı & Hakkaniyet",
                orientation="SYNTHESIS_BRIDGE",
                core_argument="Her iki kutbun meşru kaygılarını dengeleyen kademeli bir denetim mekanizması oluşturulmalıdır.",
                underlying_value="Denge & Ölçülülük",
            ),
        ]

    @classmethod
    def check_bias(cls, content_text: str) -> tuple[bool, float, list[str], dict[str, str]]:
        flagged: list[str] = []
        suggestions: dict[str, str] = {}
        content_lower = content_text.lower()

        for term, neutral_alt in cls.BIASED_LOADED_TERMS.items():
            if term in content_lower:
                flagged.append(term)
                suggestions[term] = neutral_alt

        is_neutral = len(flagged) == 0
        score = max(0.0, round(1.0 - (len(flagged) * 0.15), 2))
        return is_neutral, score, flagged, suggestions

    @classmethod
    def compose_summary(cls, raw_material: str, target_length: int = 300) -> str:
        clean = " ".join(raw_material.split())
        if len(clean) <= target_length:
            return clean
        truncated = clean[: target_length - 3].rsplit(" ", 1)[0]
        return truncated + "..."


@ai_editorial_router.post(
    "/extract-claims",
    response_model=ExtractClaimsResponse,
    summary="AI-assisted claim extraction (CAP-060)",
)
def extract_claims(request: ExtractClaimsRequest) -> ExtractClaimsResponse:
    claims = AiEditorialAssistanceService.extract_claims(
        request.source_text,
        request.max_claims,
    )
    return ExtractClaimsResponse(
        extracted_claims=claims,
        model_used="provider-neutral-kefe-nlp-v1",
        processed_at=datetime.now(UTC),
        editorial_disclaimer="AI-assisted claims require mandatory human editorial approval before publication.",
    )


@ai_editorial_router.post(
    "/suggest-perspectives",
    response_model=SuggestPerspectivesResponse,
    summary="AI-assisted perspective generation (CAP-060)",
)
def suggest_perspectives(
    request: SuggestPerspectivesRequest,
) -> SuggestPerspectivesResponse:
    perspectives = AiEditorialAssistanceService.suggest_perspectives(
        request.dilemma_title,
        request.context_summary,
    )
    return SuggestPerspectivesResponse(
        perspectives=perspectives,
        balance_entropy=0.88,
        generated_at=datetime.now(UTC),
    )


@ai_editorial_router.post(
    "/bias-check",
    response_model=BiasCheckResponse,
    summary="AI-assisted editorial bias and neutrality audit (CAP-060)",
)
def check_bias(request: BiasCheckRequest) -> BiasCheckResponse:
    is_neutral, score, flagged, suggestions = AiEditorialAssistanceService.check_bias(
        request.content_text
    )
    return BiasCheckResponse(
        is_neutral=is_neutral,
        neutrality_score=score,
        flagged_terms=flagged,
        suggested_neutral_rephrasings=suggestions,
        checked_at=datetime.now(UTC),
    )


@ai_editorial_router.post(
    "/compose-summary",
    response_model=ComposeSummaryResponse,
    summary="AI-assisted non-normative summary composition (CAP-060)",
)
def compose_summary(request: ComposeSummaryRequest) -> ComposeSummaryResponse:
    summary_text = AiEditorialAssistanceService.compose_summary(
        request.raw_material,
        request.target_length_chars,
    )
    return ComposeSummaryResponse(
        composed_summary=summary_text,
        character_count=len(summary_text),
        readability_index=0.86,
        composed_at=datetime.now(UTC),
    )

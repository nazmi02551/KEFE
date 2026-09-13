# bootstrap_catalog.py
# Auto-generates InMemory CaseVersion entries from beta_catalog.py
# for use when KEFE_PERSISTENCE_BACKEND=memory (no PostgreSQL required).
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid5

from kefe_api.infrastructure.beta_catalog import BETA_CATALOG, CATALOG_NAMESPACE
from kefe_api.modules.decision.models import (
    CaseVersion,
    FlowStep,
    PerspectiveCard,
    PerspectiveMode,
    PerspectiveSlot,
    PerspectiveSnapshot,
    PerspectiveSourceKind,
    Question,
    ReasonModerationState,
    ResolvedFlow,
    RevealSnapshot,
)

_SLOT_MAP: dict[str, PerspectiveSlot] = {
    "NEAR": PerspectiveSlot.NEAR,
    "OPPOSING": PerspectiveSlot.OPPOSING,
    "BRIDGE": PerspectiveSlot.BRIDGE,
    "ALTERNATIVE_CONTEXT": PerspectiveSlot.ALTERNATIVE_CONTEXT,
}

_STANDARD_FLOW = ResolvedFlow(
    template_code="STANDARD_COMMIT_REVEAL",
    template_version_no=1,
    entry_step_code="CONTEXT",
    steps=(
        FlowStep(
            code="CONTEXT",
            primitive_code="CONTEXT",
            capability_codes=("SOURCE_REVEAL",),
            next_step_codes=("DECISION",),
        ),
        FlowStep(
            code="DECISION",
            primitive_code="DECISION",
            capability_codes=(
                "COMMIT_FIRST",
                "CONFIDENCE_CAPTURE",
                "REASON_CAPTURE",
            ),
            next_step_codes=("RESULT",),
        ),
        FlowStep(
            code="RESULT",
            primitive_code="COLLECTIVE_RESULT",
        ),
    ),
)

_REASON_SCHEMA = {
    "tags": ["FAIRNESS", "NEED", "RESPONSIBILITY", "PRACTICAL_IMPACT"],
    "max_tags": 3,
    "text_enabled": True,
    "text_max_length": 500,
}


def build_catalog_cases() -> tuple[
    list[CaseVersion],
    list[RevealSnapshot],
    list[PerspectiveSnapshot],
]:
    generated_at = datetime.now(UTC)
    cases: list[CaseVersion] = []
    reveals: list[RevealSnapshot] = []
    perspectives: list[PerspectiveSnapshot] = []

    for index, item in enumerate(BETA_CATALOG):
        question_id = uuid5(CATALOG_NAMESPACE, f"question:{item.slug}:primary")
        confidence_id = uuid5(CATALOG_NAMESPACE, f"question:{item.slug}:confidence")

        case = CaseVersion(
            id=item.version_id,
            case_id=item.case_id,
            title=item.title,
            summary=item.summary,
            base_format=item.base_format,
            primary_domain=item.domain,
            content_risk="L0",
            version_no=1,
            questions=(
                Question(
                    id=question_id,
                    prompt=item.prompt,
                    response_type="SINGLE_CHOICE",
                    required=True,
                    response_schema={
                        "options": [item.option_a, item.option_b],
                        "reason": _REASON_SCHEMA,
                    },
                ),
                Question(
                    id=confidence_id,
                    prompt="Bu kararından ne kadar eminsin?",
                    response_type="CONFIDENCE",
                    required=False,
                    response_schema={"min": 1, "max": 10, "step": 1},
                ),
            ),
            resolved_flow=_STANDARD_FLOW,
        )

        # Simulated result snapshot
        a_share = round(0.48 + ((index % 5) * 0.02), 2)
        b_share = round(1.0 - a_share, 2)
        reveal = RevealSnapshot(
            case_version_id=item.version_id,
            layer="TRUSTED",
            n=300 + index * 7,
            confidence="MEDIUM",
            generated_at=generated_at,
            payload={item.option_a: a_share, item.option_b: b_share},
        )

        # Perspective cards from catalog
        cards = []
        for persp_idx, persp in enumerate(item.perspectives):
            slot = _SLOT_MAP.get(persp.slot, PerspectiveSlot.BRIDGE)
            persp_id = uuid5(
                CATALOG_NAMESPACE,
                f"perspective:{item.slug}:{persp.slot}:{persp_idx}",
            )
            cards.append(
                PerspectiveCard(
                    perspective_id=persp_id,
                    slot=slot,
                    body=persp.body,
                    source_kind=PerspectiveSourceKind.CURATED,
                    provenance_label="KEFE beta editoryal",
                    moderation_state=ReasonModerationState.NOT_REQUIRED,
                )
            )

        # Fallback bridge if no perspectives defined
        if not cards:
            fallback_id = uuid5(CATALOG_NAMESPACE, f"perspective:{item.slug}:bridge:0")
            cards.append(
                PerspectiveCard(
                    perspective_id=fallback_id,
                    slot=PerspectiveSlot.BRIDGE,
                    body=(
                        f"{item.option_a} yaklaşımı ile {item.option_b} yaklaşımı "
                        "farklı değerleri koruyabilir; kararın bağlama göre değişebileceğini "
                        "birlikte düşün."
                    ),
                    source_kind=PerspectiveSourceKind.CURATED,
                    provenance_label="KEFE beta editoryal",
                    moderation_state=ReasonModerationState.NOT_REQUIRED,
                )
            )

        perspective = PerspectiveSnapshot(
            case_version_id=item.version_id,
            mode=PerspectiveMode.DEGRADED_CURATED,
            sample_kind="CURATED_FALLBACK",
            sample_size=len(cards),
            generated_at=generated_at,
            provenance_note="KEFE beta editoryal fixture; topluluk gerekçesi içermez.",
            cards=tuple(cards),
        )

        cases.append(case)
        reveals.append(reveal)
        perspectives.append(perspective)

    return cases, reveals, perspectives
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.content_configuration.models import (
    CapabilityDefinition,
    ContentConfigLifecycle,
    ContentConfigurationSnapshot,
    FlowStepDefinition,
    FlowTemplateDefinition,
    PrimitiveDefinition,
    TaxonomyItem,
)

DEFAULT_CONFIG_ID = UUID("77777777-7777-4777-8777-777777777777")


def _item(code: str) -> TaxonomyItem:
    return TaxonomyItem(code=code, label_key=f"taxonomy.{code.lower()}")


def _primitive(code: str) -> PrimitiveDefinition:
    return PrimitiveDefinition(code=code, label_key=f"primitive.{code.lower()}")


def _capability(code: str, *primitive_codes: str) -> CapabilityDefinition:
    return CapabilityDefinition(
        code=code,
        label_key=f"capability.{code.lower()}",
        compatible_primitive_codes=frozenset(primitive_codes),
    )


def build_default_content_configuration() -> ContentConfigurationSnapshot:
    domains = (
        "CIVIC_POLITICS",
        "LAW_JUSTICE",
        "SPORTS",
        "TECHNOLOGY_AI",
        "WORK_BUSINESS",
        "EDUCATION",
        "FAMILY_PARENTING",
        "RELATIONSHIPS",
        "ECONOMY_MONEY",
        "HEALTH_BIOETHICS",
        "SCIENCE_FUTURE",
        "PLANET_ANIMALS",
        "CITY_PUBLIC_LIFE",
        "CULTURE_MEDIA",
        "WORLD_GEOPOLITICS",
        "DAILY_LIFE",
    )
    formats = ("TODAY", "DILEMMA", "LAB", "VS", "CALL", "DECIDE", "RETRO")
    modifiers = (
        "BLIND_FIRST",
        "PROGRESSIVE_DISCLOSURE",
        "IDENTITY_REVEAL",
        "SOURCE_REVEAL",
        "OUTCOME_REVEAL",
        "EXPERT_COMPARE",
        "OFFICIAL_DECISION_COMPARE",
        "CROSS_COUNTRY",
        "EVOLVE",
        "SENSITIVE_MODE",
        "CIVIC_INTEGRITY",
        "CONFIDENCE_CAPTURE",
        "REASON_CAPTURE",
    )
    primitives = tuple(
        _primitive(code)
        for code in (
            "CONTEXT",
            "DECISION",
            "COLLECTIVE_RESULT",
            "REFLECTION",
        )
    )
    capabilities = (
        _capability("PRINCIPLE_FIRST", "DECISION"),
        _capability("COMMIT_FIRST", "DECISION"),
        _capability("ACTOR_BLIND", "CONTEXT"),
        _capability("SOURCE_BLIND", "CONTEXT"),
        _capability("EVIDENCE_REVEAL", "CONTEXT"),
        _capability("SOURCE_REVEAL", "CONTEXT"),
        _capability("ACTOR_REVEAL", "CONTEXT"),
        _capability("ROLE_FLIP", "DECISION"),
        _capability("COUNTERARGUMENT", "CONTEXT"),
        _capability("RESPONSIBILITY_ANALYSIS", "CONTEXT"),
        _capability("PROCESS_ANALYSIS", "CONTEXT"),
        _capability("INCENTIVE_MAP", "CONTEXT"),
        _capability("THRESHOLD_ANALYSIS", "DECISION"),
        _capability("FAIRNESS_MODEL_COMPARISON", "DECISION"),
        _capability("POLICY_SIMULATOR", "DECISION"),
        _capability("STAKEHOLDER_ANALYSIS", "CONTEXT"),
        _capability("CONFIDENCE_CAPTURE", "DECISION"),
        _capability("REASON_CAPTURE", "DECISION"),
        _capability("REFLECTION", "REFLECTION"),
        _capability("INSTITUTION_RESPONSE", "CONTEXT"),
        _capability("IMPACT_TRACKING"),
    )
    flow_templates = (
        FlowTemplateDefinition(
            code="STANDARD_COMMIT_REVEAL",
            version_no=1,
            label_key="flow.standard_commit_reveal",
            entry_step_code="CONTEXT",
            steps=(
                FlowStepDefinition(
                    code="CONTEXT",
                    primitive_code="CONTEXT",
                    capability_codes=("SOURCE_REVEAL",),
                    next_step_codes=("DECISION",),
                ),
                FlowStepDefinition(
                    code="DECISION",
                    primitive_code="DECISION",
                    capability_codes=(
                        "COMMIT_FIRST",
                        "CONFIDENCE_CAPTURE",
                        "REASON_CAPTURE",
                    ),
                    next_step_codes=("RESULT",),
                ),
                FlowStepDefinition(
                    code="RESULT",
                    primitive_code="COLLECTIVE_RESULT",
                ),
            ),
        ),
        FlowTemplateDefinition(
            code="PRINCIPLE_CONTEXT_RETEST",
            version_no=1,
            label_key="flow.principle_context_retest",
            entry_step_code="PRINCIPLE",
            steps=(
                FlowStepDefinition(
                    code="PRINCIPLE",
                    primitive_code="DECISION",
                    capability_codes=("PRINCIPLE_FIRST",),
                    next_step_codes=("CONTEXT",),
                ),
                FlowStepDefinition(
                    code="CONTEXT",
                    primitive_code="CONTEXT",
                    capability_codes=("COUNTERARGUMENT",),
                    next_step_codes=("FINAL_DECISION",),
                ),
                FlowStepDefinition(
                    code="FINAL_DECISION",
                    primitive_code="DECISION",
                    capability_codes=(
                        "COMMIT_FIRST",
                        "CONFIDENCE_CAPTURE",
                        "REASON_CAPTURE",
                    ),
                    next_step_codes=("REFLECTION",),
                ),
                FlowStepDefinition(
                    code="REFLECTION",
                    primitive_code="REFLECTION",
                    capability_codes=("REFLECTION",),
                ),
            ),
        ),
    )
    return ContentConfigurationSnapshot(
        id=DEFAULT_CONFIG_ID,
        version_no=1,
        state=ContentConfigLifecycle.PUBLISHED,
        domains=tuple(_item(code) for code in domains),
        topics=(),
        base_formats=tuple(_item(code) for code in formats),
        modifiers=tuple(_item(code) for code in modifiers),
        modifier_compatibility={
            "TODAY": frozenset(
                {
                    "PROGRESSIVE_DISCLOSURE",
                    "SOURCE_REVEAL",
                    "EVOLVE",
                    "SENSITIVE_MODE",
                    "CIVIC_INTEGRITY",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "DILEMMA": frozenset(
                {
                    "BLIND_FIRST",
                    "PROGRESSIVE_DISCLOSURE",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "LAB": frozenset(
                {
                    "BLIND_FIRST",
                    "IDENTITY_REVEAL",
                    "SOURCE_REVEAL",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "VS": frozenset({"BLIND_FIRST", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
            "CALL": frozenset(
                {
                    "BLIND_FIRST",
                    "OFFICIAL_DECISION_COMPARE",
                    "EXPERT_COMPARE",
                    "EVOLVE",
                    "CONFIDENCE_CAPTURE",
                    "REASON_CAPTURE",
                }
            ),
            "DECIDE": frozenset({"EVOLVE", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
            "RETRO": frozenset({"OUTCOME_REVEAL", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}),
        },
        primitives=primitives,
        capabilities=capabilities,
        flow_templates=flow_templates,
        risks=frozenset({"L0", "L1", "L2", "L3"}),
        claim_states=frozenset({"VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"}),
        source_kinds=frozenset({"OFFICIAL", "NEWS", "RESEARCH", "EDITORIAL", "OTHER"}),
        disclosure_levels=frozenset({"ESSENTIAL", "DETAIL"}),
        created_by="system:bootstrap",
        created_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )

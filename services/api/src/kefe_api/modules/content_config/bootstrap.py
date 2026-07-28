from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType
from uuid import UUID

from kefe_api.modules.content_config.models import (
    ContentConfigLifecycle,
    ContentConfigurationSnapshot,
)

BASELINE_CONFIG_ID = UUID("77777777-7777-4777-8777-777777777777")


def baseline_configuration() -> ContentConfigurationSnapshot:
    allowed_modifiers = {
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
            {"BLIND_FIRST", "PROGRESSIVE_DISCLOSURE", "CONFIDENCE_CAPTURE", "REASON_CAPTURE"}
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
    }
    modifiers = frozenset(item for values in allowed_modifiers.values() for item in values)
    return ContentConfigurationSnapshot(
        id=BASELINE_CONFIG_ID,
        version_no=1,
        state=ContentConfigLifecycle.PUBLISHED,
        domains=frozenset(
            {
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
            }
        ),
        base_formats=frozenset({"TODAY", "DILEMMA", "LAB", "VS", "CALL", "DECIDE", "RETRO"}),
        modifiers=modifiers,
        risks=frozenset({"L0", "L1", "L2", "L3"}),
        claim_states=frozenset({"VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"}),
        review_modes=frozenset({"EDITORIAL", "TRUST", "CIVIC", "LEGAL", "SAFETY"}),
        allowed_modifiers=MappingProxyType(allowed_modifiers),
        review_modes_by_risk=MappingProxyType(
            {
                "L0": frozenset({"EDITORIAL"}),
                "L1": frozenset({"EDITORIAL", "TRUST"}),
                "L2": frozenset({"EDITORIAL", "TRUST", "SAFETY"}),
                "L3": frozenset({"EDITORIAL", "TRUST", "SAFETY"}),
            }
        ),
        created_at=datetime(2026, 7, 28, tzinfo=UTC),
        published_at=datetime(2026, 7, 28, tzinfo=UTC),
    )

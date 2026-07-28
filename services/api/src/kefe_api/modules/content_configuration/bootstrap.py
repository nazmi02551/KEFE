from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    ContentConfigurationSnapshot,
    TaxonomyItem,
)

DEFAULT_CONFIG_ID = UUID("77777777-7777-4777-8777-777777777777")


def _item(code: str) -> TaxonomyItem:
    return TaxonomyItem(code=code, label_key=f"taxonomy.{code.lower()}")


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
        risks=frozenset({"L0", "L1", "L2", "L3"}),
        claim_states=frozenset({"VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"}),
        source_kinds=frozenset({"OFFICIAL", "NEWS", "RESEARCH", "EDITORIAL", "OTHER"}),
        disclosure_levels=frozenset({"ESSENTIAL", "DETAIL"}),
        created_by="system:bootstrap",
        created_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )

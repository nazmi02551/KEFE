"""User-Controlled Discovery Profile Domain Service (CAP-077).

Replaces engagement-maximizing algorithmic black boxes with explicit,
transparent, user-governed exploration criteria.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class DomainPreference(str, Enum):
    CIVIC = "CIVIC"
    TECHNOLOGY = "TECHNOLOGY"
    BIOETHICS = "BIOETHICS"
    ENVIRONMENT = "ENVIRONMENT"
    JUSTICE = "JUSTICE"
    ECONOMIC = "ECONOMIC"


class ComplexityLevel(str, Enum):
    INTRODUCTORY = "INTRODUCTORY"
    BALANCED = "BALANCED"
    DEEP_DELIBERATION = "DEEP_DELIBERATION"


class FreshnessPreference(str, Enum):
    CURRENT_EVENTS = "CURRENT_EVENTS"
    BALANCED = "BALANCED"
    TIMELESS_FOUNDATIONS = "TIMELESS_FOUNDATIONS"


class RealEventPreference(str, Enum):
    REAL_EVENTS_FIRST = "REAL_EVENTS_FIRST"
    BALANCED = "BALANCED"
    HYPOTHETICALS_FIRST = "HYPOTHETICALS_FIRST"


@dataclass(frozen=True)
class UserDiscoveryProfile:
    user_id: str
    preferred_domains: list[DomainPreference]
    complexity_level: ComplexityLevel
    freshness_preference: FreshnessPreference
    real_event_preference: RealEventPreference
    diversification_boost: float
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "preferred_domains": [d.value for d in self.preferred_domains],
            "complexity_level": self.complexity_level.value,
            "freshness_preference": self.freshness_preference.value,
            "real_event_preference": self.real_event_preference.value,
            "diversification_boost": self.diversification_boost,
            "updated_at": self.updated_at.isoformat(),
        }


class UserDiscoveryProfileService:
    """In-memory profile store with transparent default configuration."""

    def __init__(self) -> None:
        self._profiles: dict[str, UserDiscoveryProfile] = {}

    def get_profile(self, user_id: str) -> UserDiscoveryProfile:
        if user_id in self._profiles:
            return self._profiles[user_id]

        # Constitutional balanced default profile
        return UserDiscoveryProfile(
            user_id=user_id,
            preferred_domains=[
                DomainPreference.CIVIC,
                DomainPreference.TECHNOLOGY,
                DomainPreference.BIOETHICS,
                DomainPreference.JUSTICE,
            ],
            complexity_level=ComplexityLevel.BALANCED,
            freshness_preference=FreshnessPreference.BALANCED,
            real_event_preference=RealEventPreference.BALANCED,
            diversification_boost=0.5,
            updated_at=datetime.now(UTC),
        )

    def update_profile(
        self,
        user_id: str,
        preferred_domains: list[DomainPreference],
        complexity_level: ComplexityLevel,
        freshness_preference: FreshnessPreference,
        real_event_preference: RealEventPreference,
        diversification_boost: float,
    ) -> UserDiscoveryProfile:
        clamped_boost = max(0.0, min(1.0, diversification_boost))
        profile = UserDiscoveryProfile(
            user_id=user_id,
            preferred_domains=list(preferred_domains),
            complexity_level=complexity_level,
            freshness_preference=freshness_preference,
            real_event_preference=real_event_preference,
            diversification_boost=clamped_boost,
            updated_at=datetime.now(UTC),
        )
        self._profiles[user_id] = profile
        return profile

from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.discovery.user_discovery_profile import (
    ComplexityLevel,
    DomainPreference,
    FreshnessPreference,
    RealEventPreference,
    UserDiscoveryProfileService,
)


def test_user_controlled_discovery_api_get_default_profile() -> None:
    app = create_app()
    client = TestClient(app)

    user_id = "test-user-alpha"
    res = client.get(f"/v1/discovery/profile?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["user_id"] == user_id
    assert "CIVIC" in data["preferred_domains"]
    assert data["complexity_level"] == "BALANCED"
    assert data["freshness_preference"] == "BALANCED"
    assert data["real_event_preference"] == "BALANCED"
    assert data["diversification_boost"] == 0.5
    assert "updated_at" in data


def test_user_controlled_discovery_api_update_profile() -> None:
    app = create_app()
    client = TestClient(app)

    user_id = "test-user-custom"
    payload = {
        "preferred_domains": ["TECHNOLOGY", "ENVIRONMENT"],
        "complexity_level": "DEEP_DELIBERATION",
        "freshness_preference": "CURRENT_EVENTS",
        "real_event_preference": "REAL_EVENTS_FIRST",
        "diversification_boost": 0.85,
    }

    put_res = client.put(f"/v1/discovery/profile?user_id={user_id}", json=payload)
    assert put_res.status_code == 200
    put_data = put_res.json()

    assert put_data["user_id"] == user_id
    assert put_data["preferred_domains"] == ["TECHNOLOGY", "ENVIRONMENT"]
    assert put_data["complexity_level"] == "DEEP_DELIBERATION"
    assert put_data["freshness_preference"] == "CURRENT_EVENTS"
    assert put_data["real_event_preference"] == "REAL_EVENTS_FIRST"
    assert put_data["diversification_boost"] == 0.85

    # Verify subsequent GET returns updated profile
    get_res = client.get(f"/v1/discovery/profile?user_id={user_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["preferred_domains"] == ["TECHNOLOGY", "ENVIRONMENT"]
    assert get_data["complexity_level"] == "DEEP_DELIBERATION"


def test_user_discovery_profile_service_boost_clamping() -> None:
    service = UserDiscoveryProfileService()
    profile = service.update_profile(
        user_id="user-clamp",
        preferred_domains=[DomainPreference.CIVIC],
        complexity_level=ComplexityLevel.INTRODUCTORY,
        freshness_preference=FreshnessPreference.TIMELESS_FOUNDATIONS,
        real_event_preference=RealEventPreference.HYPOTHETICALS_FIRST,
        diversification_boost=1.5,
    )
    assert profile.diversification_boost == 1.0

    profile_low = service.update_profile(
        user_id="user-clamp",
        preferred_domains=[DomainPreference.CIVIC],
        complexity_level=ComplexityLevel.INTRODUCTORY,
        freshness_preference=FreshnessPreference.TIMELESS_FOUNDATIONS,
        real_event_preference=RealEventPreference.HYPOTHETICALS_FIRST,
        diversification_boost=-0.5,
    )
    assert profile_low.diversification_boost == 0.0

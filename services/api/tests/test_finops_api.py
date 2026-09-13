from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_get_finops_summary() -> None:
    res = client.get("/v1/analytics/finops/summary")
    assert res.status_code == 200
    data = res.json()
    assert "cost_per_weigh_usd" in data
    assert "total_monthly_spend_usd" in data
    assert "total_tokens_consumed" in data
    assert "p95_latency_ms" in data
    assert data["cost_per_weigh_usd"] > 0
    assert data["total_monthly_spend_usd"] > 0


def test_get_finops_breakdown() -> None:
    res = client.get("/v1/analytics/finops/breakdown")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 4
    categories = [i["category"] for i in data["items"]]
    assert "LLM_INFERENCE" in categories
    assert "SMS_OTP" in categories
    assert "STORAGE_CDN" in categories
    assert data["total_spend_usd"] > 0


def test_simulate_scale() -> None:
    res = client.post(
        "/v1/analytics/finops/simulate",
        json={
            "projected_monthly_wau": 50000,
            "average_weighs_per_user": 4,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["projected_monthly_wau"] == 50000
    assert data["total_projected_weighs"] == 200000
    assert data["projected_monthly_cost_usd"] > 0
    assert data["projected_cost_per_weigh_usd"] < 0.06
    assert "breakdown_projection" in data

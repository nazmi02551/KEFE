from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import app


def test_get_signal_consensus_cards_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/v1/signals/consensus-cards")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    gold_card = data[0]
    assert gold_card["confidence_tier"] == "GOLD"
    assert gold_card["sample_size"] >= 1000
    assert gold_card["agreement_percentage"] >= 75.0
    assert "Son koltuk" in gold_card["case_title"]
    assert "Öncelikli ihtiyacı" in gold_card["consensus_statement"]

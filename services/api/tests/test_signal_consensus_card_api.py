from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.signal.in_memory import InMemorySignalRepository
from kefe_api.modules.signal.signal_models import QualifiedSignal, SignalQualificationTier


def _make_app_with_signals(signals: list[QualifiedSignal]):
    """Create a fresh app instance with pre-seeded signals in the repository."""
    app = create_app()
    repo = InMemorySignalRepository()
    for s in signals:
        repo.save_qualified_signal(s)
    app.state.signal_repository = repo
    return app


_SEED_SIGNALS = [
    QualifiedSignal(
        signal_id=UUID("77777777-7777-4777-8777-777777777701"),
        case_version_id=UUID("22222222-2222-4222-8222-222222222222"),
        case_title="Son koltuk kime verilmeli?",
        consensus_statement="Öncelikli ihtiyacı olan yurttaşlara pozitif ayrımcılık kamu vicdanında yüksek uzlaşı taşımaktadır.",
        agreement_percentage=82.4,
        sample_size=1420,
        qualification_tier=SignalQualificationTier.GOLD_STANDARD,
        methodology_version="1.0.0",
        qualification_audit_hash="a" * 64,
        certified_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC),
    ),
    QualifiedSignal(
        signal_id=UUID("77777777-7777-4777-8777-777777777702"),
        case_version_id=UUID("22222222-2222-4222-8222-222222222223"),
        case_title="Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?",
        consensus_statement="Kişisel mahremiyet ve açık rıza olmaksızın model eğitimi sınırlandırılmalıdır.",
        agreement_percentage=76.8,
        sample_size=1150,
        qualification_tier=SignalQualificationTier.SILVER_VALIDATED,
        methodology_version="1.0.0",
        qualification_audit_hash="b" * 64,
        certified_at=datetime(2026, 8, 20, 14, 30, 0, tzinfo=UTC),
    ),
    QualifiedSignal(
        signal_id=UUID("77777777-7777-4777-8777-777777777703"),
        case_version_id=UUID("22222222-2222-4222-8222-222222222225"),
        case_title="Kamu sözleşmeleri varsayılan olarak herkese açık olmalı mı?",
        consensus_statement="Ticari sır kısıtlaması daraltılarak kamu ihalelerinde tam şeffaflık sağlanmalıdır.",
        agreement_percentage=69.2,
        sample_size=780,
        qualification_tier=SignalQualificationTier.BRONZE_OBSERVED,
        methodology_version="1.0.0",
        qualification_audit_hash="c" * 64,
        certified_at=datetime(2026, 8, 25, 9, 15, 0, tzinfo=UTC),
    ),
]


def test_get_signal_consensus_cards_empty() -> None:
    """With no signals in repository the endpoint returns an empty list."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/v1/signals/consensus-cards")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_signal_consensus_cards_with_seed() -> None:
    """With seeded signals the endpoint returns them in order."""
    app = _make_app_with_signals(_SEED_SIGNALS)
    client = TestClient(app)
    response = client.get("/v1/signals/consensus-cards")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    # All items must have required fields
    for card in data:
        assert "signal_id" in card
        assert "case_version_id" in card
        assert "case_title" in card
        assert "consensus_statement" in card
        assert "agreement_percentage" in card
        assert "sample_size" in card
        assert "confidence_tier" in card
        assert "certified_at" in card
        assert "qualification_tier" in card

    # First card (newest certified_at = 2026-08-25) is BRONZE
    last_card = data[0]
    assert last_card["sample_size"] >= 100
    assert last_card["agreement_percentage"] >= 50.0


def test_get_signal_consensus_cards_pagination() -> None:
    """limit/offset parameters work correctly."""
    app = _make_app_with_signals(_SEED_SIGNALS)
    client = TestClient(app)

    resp_page1 = client.get("/v1/signals/consensus-cards?limit=2&offset=0")
    assert resp_page1.status_code == 200
    page1 = resp_page1.json()
    assert len(page1) == 2

    resp_page2 = client.get("/v1/signals/consensus-cards?limit=2&offset=2")
    assert resp_page2.status_code == 200
    page2 = resp_page2.json()
    assert len(page2) == 1

    # No overlap between pages
    ids_p1 = {c["signal_id"] for c in page1}
    ids_p2 = {c["signal_id"] for c in page2}
    assert ids_p1.isdisjoint(ids_p2)


def test_get_signal_consensus_cards_excludes_unqualified() -> None:
    """UNQUALIFIED signals are not returned in consensus cards."""
    from kefe_api.modules.signal.signal_models import SignalQualificationTier
    unqualified = QualifiedSignal(
        signal_id=UUID("77777777-7777-4777-8777-777777777799"),
        case_version_id=UUID("22222222-2222-4222-8222-222222222299"),
        case_title="Düşük katılımlı test vakası",
        consensus_statement="Yeterli katılım sağlanamadı.",
        agreement_percentage=55.0,
        sample_size=12,
        qualification_tier=SignalQualificationTier.UNQUALIFIED,
        methodology_version="1.0.0",
        qualification_audit_hash="d" * 64,
        certified_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=UTC),
    )
    app = _make_app_with_signals([unqualified])
    client = TestClient(app)
    response = client.get("/v1/signals/consensus-cards")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
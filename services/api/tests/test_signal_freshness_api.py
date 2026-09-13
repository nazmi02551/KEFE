from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.signal.in_memory import InMemorySignalRepository
from kefe_api.modules.signal.signal_models import QualifiedSignal, SignalQualificationTier

_SIGNAL_ID = UUID("77777777-7777-4777-8777-777777777701")
_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")

_SEED_SIGNAL = QualifiedSignal(
    signal_id=_SIGNAL_ID,
    case_version_id=_CASE_ID,
    case_title="Toplu Taşıma Fiyatlandırması",
    consensus_statement="Halk çoğunluğu sübvansiyonu destekliyor.",
    agreement_percentage=82.4,
    sample_size=1420,
    qualification_tier=SignalQualificationTier.GOLD_STANDARD,
    methodology_version="1.0.0",
    qualification_audit_hash="a" * 64,
    certified_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC),
)


def _make_app():
    app = create_app()
    repo = InMemorySignalRepository()
    repo.save_qualified_signal(_SEED_SIGNAL)
    app.state.signal_repository = repo
    return app


def test_signal_freshness_api_with_explicit_age() -> None:
    app = _make_app()
    client = TestClient(app)

    # 1. Fresh signal (age = 2 days, half_life = 30 days -> weight ~ 0.95 -> FRESH)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/freshness?half_life_days=30&age_days=2.0")
    assert res.status_code == 200
    data = res.json()
    assert data["signal_id"] == str(_SIGNAL_ID)
    assert data["case_version_id"] == str(_CASE_ID)
    assert data["half_life_days"] == 30
    assert data["age_days"] == 2.0
    assert data["freshness_state"] == "FRESH"
    assert data["remaining_weight"] >= 0.85

    # 2. Stable signal (age = 20 days, half_life = 30 days -> weight ~ 0.63 -> STABLE)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/freshness?half_life_days=30&age_days=20.0")
    assert res.status_code == 200
    data = res.json()
    assert data["freshness_state"] == "STABLE"
    assert 0.50 <= data["remaining_weight"] < 0.85

    # 3. Deprecating signal (age = 45 days, half_life = 30 days -> weight ~ 0.35 -> DEPRECATING)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/freshness?half_life_days=30&age_days=45.0")
    assert res.status_code == 200
    data = res.json()
    assert data["freshness_state"] == "DEPRECATING"
    assert 0.20 <= data["remaining_weight"] < 0.50

    # 4. Expired signal (age = 90 days, half_life = 30 days -> weight ~ 0.125 -> EXPIRED_NEEDS_RETEST)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/freshness?half_life_days=30&age_days=90.0")
    assert res.status_code == 200
    data = res.json()
    assert data["freshness_state"] == "EXPIRED_NEEDS_RETEST"
    assert data["remaining_weight"] < 0.20


def test_signal_freshness_api_default_computed_age() -> None:
    app = _make_app()
    client = TestClient(app)

    res = client.get(f"/v1/signals/{_SIGNAL_ID}/freshness")
    assert res.status_code == 200
    data = res.json()
    assert data["signal_id"] == str(_SIGNAL_ID)
    assert data["half_life_days"] == 30
    assert data["age_days"] > 0
    assert "freshness_state" in data
    assert "remaining_weight" in data


def test_signal_freshness_api_not_found() -> None:
    app = _make_app()
    client = TestClient(app)

    missing_id = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/v1/signals/{missing_id}/freshness")
    assert res.status_code == 404

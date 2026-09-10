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
    case_title="Son koltuk kime verilmeli?",
    consensus_statement="Öncelikli ihtiyacı olan yurttaşlara pozitif ayrımcılık kamu vicdanında yüksek uzlaşı taşımaktadır.",
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


def test_signal_scope_api() -> None:
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/scope-alignment")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["jurisdiction_level"] == "MUNICIPAL"
    assert data["alignment_status"] == "STRICTLY_ALIGNED"
    assert data["overall_alignment_score"] >= 0.85
    assert len(data["scope_seal_hash"]) == 64
    assert data["validity_window_days"] == 90
    assert "Türkiye" in data["geographic_scope"]

    dimensions = data["dimensions"]
    assert len(dimensions) == 4
    for dim in dimensions:
        assert "dimension" in dim
        assert "declared_scope" in dim
        assert "sample_scope" in dim
        assert 0.0 <= dim["alignment_score"] <= 1.0
        assert isinstance(dim["is_valid"], bool)


def test_signal_scope_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/scope-alignment")
    assert res.status_code == 404
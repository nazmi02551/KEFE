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


def test_signal_versioning_api() -> None:
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/versioning")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["current_version"] == "v1.2.0-entropy"
    assert len(data["current_methodology_hash"]) == 64
    assert data["audit_chain_valid"] is True

    snapshots = data["snapshots"]
    assert len(snapshots) == 2
    assert snapshots[0]["methodology_version"] == "v1.0.0"
    assert snapshots[0]["parent_snapshot_hash"] is None
    assert snapshots[1]["methodology_version"] == "v1.2.0-entropy"
    assert snapshots[1]["parent_snapshot_hash"] == snapshots[0]["snapshot_hash"]

    delta = data["latest_delta"]
    assert delta is not None
    assert delta["from_version"] == "v1.0.0"
    assert delta["to_version"] == "v1.2.0-entropy"
    assert delta["distribution_shift"] == 0.02


def test_signal_versioning_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/versioning")
    assert res.status_code == 404
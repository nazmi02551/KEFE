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


def test_signal_target_registry_api() -> None:
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/targets")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert len(data["registry_proof_hash"]) == 64
    assert len(data["targets"]) == 2

    primary = data["targets"][0]
    assert primary["target_id"] == data["primary_target_id"]
    assert primary["target_type"] == "MUNICIPAL_GOVERNMENT"
    assert primary["dispatch_status"] == "ACKNOWLEDGED"
    assert primary["response_due_days"] == 30
    assert "@" in primary["official_contact_channel"]


def test_signal_target_registry_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/targets")
    assert res.status_code == 404
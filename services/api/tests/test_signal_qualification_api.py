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


def test_signal_qualification_api() -> None:
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/qualification")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["qualification_status"] == "QUALIFIED"
    assert data["qualification_tier"] == "GOLD_STANDARD"
    assert data["overall_score"] >= 0.80
    assert data["sample_size"] == 1420
    assert len(data["qualification_audit_hash"]) == 64

    criteria = data["criteria"]
    assert len(criteria) == 5
    expected_crit_ids = {
        "sample_sufficiency",
        "contribution_integrity",
        "entropy_diversity",
        "deliberation_depth",
        "astroturfing_immunity",
    }
    actual_crit_ids = {c["criterion_id"] for c in criteria}
    assert actual_crit_ids == expected_crit_ids

    for c in criteria:
        assert c["is_passed"] is True
        assert len(c["name_tr"]) > 0
        assert len(c["name_en"]) > 0
        assert len(c["audit_note"]) > 0

    assert len(data["eligible_channels"]) == 4
    assert "CIVIC_PUBLIC_DASHBOARD" in data["eligible_channels"]
    assert "POLICY_DELIBERATION_REPORT" in data["eligible_channels"]


def test_signal_qualification_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/qualification")
    assert res.status_code == 404
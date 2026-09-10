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


def test_contribution_classes_api() -> None:
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/contribution-classes")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(_CASE_ID)
    # core=1420, exposed=~27% of 1420=383, advocacy=~11% of 1420=156
    assert data["total_contributions"] >= 1420
    assert data["contamination_risk_index"] == 0.0
    assert data["isolation_audit_status"] == "ENFORCED"
    assert len(data["isolation_proof_hash"]) == 64

    classes = data["classes"]
    assert len(classes) == 3
    expected_ids = {"CORE_PRE_RESULT", "EXPOSED", "ADVOCACY_SUPPORT"}
    actual_ids = {c["class_id"] for c in classes}
    assert actual_ids == expected_ids

    core = next(c for c in classes if c["class_id"] == "CORE_PRE_RESULT")
    assert core["is_signal_eligible"] is True
    assert core["count"] == 1420

    exposed = next(c for c in classes if c["class_id"] == "EXPOSED")
    assert exposed["is_signal_eligible"] is False

    advocacy = next(c for c in classes if c["class_id"] == "ADVOCACY_SUPPORT")
    assert advocacy["is_signal_eligible"] is False


def test_contribution_classes_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/contribution-classes")
    assert res.status_code == 404
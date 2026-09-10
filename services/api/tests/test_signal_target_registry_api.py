"""API tests for GET /v1/signals/{signal_id}/targets.

The endpoint now uses NullInstitutionTargetResolver by default (safe — no
auto-dispatch without explicit Admin targeting). Tests verify the endpoint
shape and the null-target case.

NOTE: When Admin target management (CAP-057) is integrated, the router will
accept an injected resolver and tests will inject StaticInstitutionTargetResolver
to verify populated responses.
"""
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


def test_signal_target_registry_api_returns_200_with_null_targets() -> None:
    """GET /targets returns 200 with empty targets list when no resolver is configured.

    NullInstitutionTargetResolver is the safe default — no auto-dispatch without
    explicit institutional targeting (CAP-057 Admin Signal Target Ops).
    """
    app = _make_app()
    client = TestClient(app)

    signal_id = str(_SIGNAL_ID)
    res = client.get(f"/v1/signals/{signal_id}/targets")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert len(data["registry_proof_hash"]) == 64
    # NullResolver: no targets pre-assigned
    assert data["targets"] == []
    assert data["primary_target_id"] is None
    assert data["case_version_id"] == str(_CASE_ID)


def test_signal_target_registry_api_response_shape() -> None:
    """Verify the response model fields are present and well-typed."""
    app = _make_app()
    client = TestClient(app)

    res = client.get(f"/v1/signals/{_SIGNAL_ID}/targets")
    assert res.status_code == 200
    data = res.json()

    required_fields = {"signal_id", "case_version_id", "primary_target_id",
                       "targets", "certified_at", "registry_proof_hash"}
    assert required_fields.issubset(data.keys())
    assert isinstance(data["targets"], list)
    assert isinstance(data["certified_at"], str)


def test_signal_target_registry_not_found() -> None:
    app = create_app()  # empty repository
    client = TestClient(app)
    res = client.get(f"/v1/signals/{_SIGNAL_ID}/targets")
    assert res.status_code == 404
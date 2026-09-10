"""API tests for signal dispatch target endpoints (CAP-057 Phase 2).

Covers:
- POST /internal/signal-pipeline/signals/{id}/propose-target
- POST /internal/signal-pipeline/signals/{id}/advance-target

Tests use in-memory mode (no PostgresSignalDispatchTargetWriter in app state).
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
_TARGET_ID = UUID("cccccccc-3333-4ccc-8ccc-333333333333")

_PUBLISHED_SIGNAL = QualifiedSignal(
    signal_id=_SIGNAL_ID,
    case_version_id=_CASE_ID,
    case_title="Kamu sözleşmeleri açık olmalı mı?",
    consensus_statement=(
        "Ticari sır kısıtlaması daraltılarak kamu ihalelerinde tam şeffaflık sağlanmalıdır."
    ),
    agreement_percentage=69.2,
    sample_size=780,
    qualification_tier=SignalQualificationTier.BRONZE_OBSERVED,
    methodology_version="1.0.0",
    qualification_audit_hash="c" * 64,
    certified_at=datetime(2026, 8, 25, 9, 15, 0, tzinfo=UTC),
)

_PROVISIONAL_SIGNAL = QualifiedSignal(
    signal_id=UUID("77777777-7777-4777-8777-777777777799"),
    case_version_id=UUID("22222222-2222-4222-8222-222222222299"),
    case_title="Düşük katılımlı test",
    consensus_statement=(
        "[PROVISIONAL] 'Düşük katılımlı test' meselesinde katılımcıların %55.0'i "
        "'opt_a' yönünde taahhüt etmiştir. Bu ifade editoryal inceleme sürecinden geçmemiştir."
    ),
    agreement_percentage=55.0,
    sample_size=12,
    qualification_tier=SignalQualificationTier.UNQUALIFIED,
    methodology_version="1.0.0",
    qualification_audit_hash="d" * 64,
    certified_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=UTC),
)


def _make_app(signals=None):
    app = create_app()
    repo = InMemorySignalRepository()
    for s in (signals or [_PUBLISHED_SIGNAL]):
        repo.save_qualified_signal(s)
    app.state.signal_repository = repo
    return app


class TestProposeTarget:
    def test_propose_target_201(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/propose-target",
            json={
                "target_id": str(_TARGET_ID),
                "target_name": "Test Düzenleyici Kurum",
                "target_type": "REGULATORY_BODY",
                "jurisdiction_level": "NATIONAL",
                "official_contact_channel": "contact@test.gov.tr",
                "response_due_days": 21,
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["signal_id"] == str(_SIGNAL_ID)
        assert data["target_id"] == str(_TARGET_ID)
        assert data["dispatch_status"] == "PROPOSED_TARGET"
        assert "in-memory" in data["message"]

    def test_propose_target_blocks_provisional(self) -> None:
        prov_id = _PROVISIONAL_SIGNAL.signal_id
        app = _make_app(signals=[_PROVISIONAL_SIGNAL])
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{prov_id}/propose-target",
            json={
                "target_id": str(_TARGET_ID),
                "target_name": "Test Kurum",
                "target_type": "REGULATORY_BODY",
                "jurisdiction_level": "NATIONAL",
                "official_contact_channel": "contact@test.gov.tr",
            },
        )
        assert res.status_code == 400
        assert "PROVISIONAL" in res.json()["detail"]

    def test_propose_target_invalid_target_type(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/propose-target",
            json={
                "target_id": str(_TARGET_ID),
                "target_name": "Test Kurum",
                "target_type": "INVALID_TYPE",
                "jurisdiction_level": "NATIONAL",
                "official_contact_channel": "contact@test.gov.tr",
            },
        )
        assert res.status_code == 400
        assert "INVALID_TYPE" in res.json()["detail"]

    def test_propose_target_signal_not_found(self) -> None:
        app = _make_app()
        client = TestClient(app)

        missing = UUID("00000000-0000-4000-8000-000000000000")
        res = client.post(
            f"/internal/signal-pipeline/signals/{missing}/propose-target",
            json={
                "target_id": str(_TARGET_ID),
                "target_name": "Test Kurum",
                "target_type": "REGULATORY_BODY",
                "jurisdiction_level": "NATIONAL",
                "official_contact_channel": "contact@test.gov.tr",
            },
        )
        assert res.status_code == 404


class TestAdvanceTarget:
    def test_advance_target_verified_in_memory(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/advance-target",
            json={
                "target_id": str(_TARGET_ID),
                "next_status": "VERIFIED_TARGET",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_status"] == "VERIFIED_TARGET"
        assert "in-memory" in data["message"]

    def test_advance_target_dispatched_in_memory(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/advance-target",
            json={
                "target_id": str(_TARGET_ID),
                "next_status": "DISPATCHED",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_status"] == "DISPATCHED"

    def test_advance_target_declined_in_memory(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/advance-target",
            json={
                "target_id": str(_TARGET_ID),
                "next_status": "DECLINED_JURISDICTION",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_status"] == "DECLINED_JURISDICTION"

    def test_advance_target_invalid_status(self) -> None:
        app = _make_app()
        client = TestClient(app)

        res = client.post(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/advance-target",
            json={
                "target_id": str(_TARGET_ID),
                "next_status": "NOT_A_STATUS",
            },
        )
        assert res.status_code == 400

    def test_advance_target_signal_not_found(self) -> None:
        app = _make_app()
        client = TestClient(app)

        missing = UUID("00000000-0000-4000-8000-000000000001")
        res = client.post(
            f"/internal/signal-pipeline/signals/{missing}/advance-target",
            json={
                "target_id": str(_TARGET_ID),
                "next_status": "DISPATCHED",
            },
        )
        assert res.status_code == 404
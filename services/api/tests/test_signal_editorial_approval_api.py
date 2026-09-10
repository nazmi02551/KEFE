"""API tests for editorial CQB approval endpoint (CAP-063).

PUT /internal/signal-pipeline/signals/{signal_id}/approve-statement

Covers:
- Successful approval of provisional signal
- Blocks if statement still contains [PROVISIONAL]
- Blocks if signal is not provisional
- 404 if signal not found
- Blank statement validation
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
_PROV_SIGNAL_ID = UUID("77777777-7777-4777-8777-777777777799")


def _make_provisional_signal(signal_id: UUID = _PROV_SIGNAL_ID) -> QualifiedSignal:
    return QualifiedSignal(
        signal_id=signal_id,
        case_version_id=_CASE_ID,
        case_title="Düşük katılımlı test vakası",
        consensus_statement=(
            "[PROVISIONAL] 'Düşük katılımlı test vakası' meselesinde katılımcıların %55.0'i "
            "'opt_a' yönünde taahhüt etmiştir. Bu ifade editoryal inceleme sürecinden geçmemiştir."
        ),
        agreement_percentage=55.0,
        sample_size=12,
        qualification_tier=SignalQualificationTier.UNQUALIFIED,
        methodology_version="1.0.0",
        qualification_audit_hash="d" * 64,
        certified_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=UTC),
    )


def _make_approved_signal() -> QualifiedSignal:
    return QualifiedSignal(
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


def _make_app(signals):
    app = create_app()
    repo = InMemorySignalRepository()
    for s in signals:
        repo.save_qualified_signal(s)
    app.state.signal_repository = repo
    return app


class TestApproveConsensusStatement:
    def test_approve_provisional_signal_200(self) -> None:
        app = _make_app([_make_provisional_signal()])
        client = TestClient(app)

        res = client.put(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "Test vakasında katılımcıların çoğunluğu opt_a seçeneğini desteklemiştir."},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["signal_id"] == str(_PROV_SIGNAL_ID)
        assert data["is_provisional"] is False
        assert "[PROVISIONAL]" not in data["approved_statement"]
        assert "eligible for dispatch" in data["message"]
        assert len(data["qualification_audit_hash"]) == 64

    def test_approve_updates_signal_in_repo(self) -> None:
        """After approval, get_signal no longer returns [PROVISIONAL]."""
        app = _make_app([_make_provisional_signal()])
        client = TestClient(app)

        client.put(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "Onaylanmış ifade: test vakası uzlaşısı."},
        )

        get_res = client.get(f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert "[PROVISIONAL]" not in data["consensus_statement"]
        assert data["is_provisional"] is False

    def test_approve_blocks_if_statement_still_provisional(self) -> None:
        app = _make_app([_make_provisional_signal()])
        client = TestClient(app)

        res = client.put(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "[PROVISIONAL] bu hâlâ taslak"},
        )
        assert res.status_code == 400
        assert "PROVISIONAL" in res.json()["detail"]

    def test_approve_blocks_blank_statement(self) -> None:
        app = _make_app([_make_provisional_signal()])
        client = TestClient(app)

        res = client.put(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "   "},
        )
        assert res.status_code == 400
        assert "blank" in res.json()["detail"].lower()

    def test_approve_blocks_if_already_approved(self) -> None:
        """Signal without [PROVISIONAL] tag should reject approval."""
        app = _make_app([_make_approved_signal()])
        client = TestClient(app)

        res = client.put(
            f"/internal/signal-pipeline/signals/{_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "Yeni ifade deneme."},
        )
        assert res.status_code == 400
        assert "not contain [PROVISIONAL]" in res.json()["detail"]

    def test_approve_signal_not_found_404(self) -> None:
        app = _make_app([])
        client = TestClient(app)

        missing = UUID("00000000-0000-4000-8000-000000000099")
        res = client.put(
            f"/internal/signal-pipeline/signals/{missing}/approve-statement",
            json={"approved_statement": "Herhangi bir ifade."},
        )
        assert res.status_code == 404

    def test_approve_then_dispatch_eligible(self) -> None:
        """After approval, propose-target should succeed (no longer blocked by PROVISIONAL)."""
        target_id = UUID("cccccccc-3333-4ccc-8ccc-333333333333")
        app = _make_app([_make_provisional_signal()])
        client = TestClient(app)

        # Approve first
        client.put(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/approve-statement",
            json={"approved_statement": "Onaylanmış ifade — dispatch için hazır."},
        )

        # Then propose target
        res = client.post(
            f"/internal/signal-pipeline/signals/{_PROV_SIGNAL_ID}/propose-target",
            json={
                "target_id": str(target_id),
                "target_name": "Test Kurum",
                "target_type": "REGULATORY_BODY",
                "jurisdiction_level": "NATIONAL",
                "official_contact_channel": "contact@test.gov.tr",
            },
        )
        assert res.status_code == 201
        assert res.json()["dispatch_status"] == "PROPOSED_TARGET"
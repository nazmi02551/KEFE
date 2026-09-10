"""Tests for Signal Pipeline Admin API endpoints.

Covers:
- POST /internal/signal-pipeline/compute â€” returns 204 when no data, 200 with computed signal.
- GET /internal/signal-pipeline/signals â€” list all computed signals.
- GET /internal/signal-pipeline/signals/{id} â€” get single signal by ID.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.signal.in_memory import InMemorySignalRepository
from kefe_api.modules.signal.pipeline_service import SignalPipelineService
from kefe_api.modules.signal.signal_models import SignalComputationInput

_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")
_NOW = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)


def _make_app_with_repo(repo: InMemorySignalRepository):
    app = create_app()
    app.state.signal_repository = repo
    app.state.signal_pipeline_service = SignalPipelineService(
        repository=repo,
        clock=lambda: _NOW,
    )
    return app


def _make_input(core_commit_count: int = 500) -> SignalComputationInput:
    return SignalComputationInput(
        case_version_id=_CASE_ID,
        case_title="Son koltuk kime verilmeli?",
        core_commit_count=core_commit_count,
        top_stance_code="EVET",
        top_stance_count=int(core_commit_count * 0.82),
        agreement_percentage=82.0,
        stance_distribution={"EVET": 0.82, "HAYIR": 0.18},
        computed_at=_NOW,
    )


class TestSignalComputeEndpoint:
    def test_returns_204_when_no_data(self) -> None:
        repo = InMemorySignalRepository()
        client = TestClient(_make_app_with_repo(repo))

        res = client.post(
            "/internal/signal-pipeline/compute",
            json={"case_version_id": str(_CASE_ID)},
        )
        assert res.status_code == 204

    def test_returns_200_with_computed_signal(self) -> None:
        repo = InMemorySignalRepository()
        repo.seed_computation_input(_make_input())
        client = TestClient(_make_app_with_repo(repo))

        res = client.post(
            "/internal/signal-pipeline/compute",
            json={"case_version_id": str(_CASE_ID)},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["case_version_id"] == str(_CASE_ID)
        assert data["qualification_tier"] == "GOLD_STANDARD"
        assert data["sample_size"] == 500
        assert data["is_provisional"] is True
        assert len(data["qualification_audit_hash"]) == 64

    def test_persists_signal_after_compute(self) -> None:
        repo = InMemorySignalRepository()
        repo.seed_computation_input(_make_input())
        client = TestClient(_make_app_with_repo(repo))

        res = client.post(
            "/internal/signal-pipeline/compute",
            json={"case_version_id": str(_CASE_ID)},
        )
        assert res.status_code == 200
        signal_id = res.json()["signal_id"]

        # The signal should be retrievable via GET
        get_res = client.get(f"/internal/signal-pipeline/signals/{signal_id}")
        assert get_res.status_code == 200
        assert get_res.json()["signal_id"] == signal_id


class TestSignalListEndpoint:
    def test_empty_list(self) -> None:
        repo = InMemorySignalRepository()
        client = TestClient(_make_app_with_repo(repo))

        res = client.get("/internal/signal-pipeline/signals")
        assert res.status_code == 200
        assert res.json() == []

    def test_lists_computed_signals(self) -> None:
        repo = InMemorySignalRepository()
        repo.seed_computation_input(_make_input())
        client = TestClient(_make_app_with_repo(repo))

        # Compute first
        client.post("/internal/signal-pipeline/compute", json={"case_version_id": str(_CASE_ID)})

        res = client.get("/internal/signal-pipeline/signals")
        assert res.status_code == 200
        assert len(res.json()) == 1


class TestSignalGetEndpoint:
    def test_returns_404_for_unknown_signal(self) -> None:
        repo = InMemorySignalRepository()
        client = TestClient(_make_app_with_repo(repo))

        res = client.get(f"/internal/signal-pipeline/signals/{_CASE_ID}")
        assert res.status_code == 404
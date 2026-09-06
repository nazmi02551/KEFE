from __future__ import annotations

from uuid import UUID
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.signal.signal_health import (
    SignalHealthAuditService,
    SignalQualificationStatus,
)


def test_signal_health_card_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/health")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["overall_qualification"] == "QUALIFIED_SIGNAL"
    assert data["overall_health_score"] > 80.0
    assert data["sample_size"] == 1420
    assert data["methodology_hash"] == "sha256-sig-health-5dim-9f82a"

    dims = data["dimensions"]
    assert len(dims) == 5
    expected_dim_ids = {
        "SAMPLE_SIZE",
        "BOT_RESISTANCE",
        "SEGMENT_ENTROPY",
        "DELIBERATION_DEPTH",
        "TEMPORAL_FRESHNESS",
    }
    actual_dim_ids = {d["dimension_id"] for d in dims}
    assert actual_dim_ids == expected_dim_ids

    for d in dims:
        assert d["is_passed"] is True
        assert len(d["title_tr"]) > 0
        assert len(d["title_en"]) > 0
        assert len(d["detail"]) > 0


def test_signal_health_audit_service_qualification_boundaries() -> None:
    service = SignalHealthAuditService()
    sig_id = UUID("77777777-7777-4777-8777-777777777701")
    case_id = UUID("22222222-2222-4222-8222-222222222222")

    # 1. Provisional Trend (low sample size, but good bot integrity)
    rep_prov = service.evaluate(
        signal_id=sig_id,
        case_version_id=case_id,
        sample_size=65,
        bot_integrity=0.90,
    )
    assert rep_prov.overall_qualification == SignalQualificationStatus.PROVISIONAL_TREND

    # 2. Unqualified Noise (poor bot integrity)
    rep_noise = service.evaluate(
        signal_id=sig_id,
        case_version_id=case_id,
        sample_size=1000,
        bot_integrity=0.45,
    )
    assert rep_noise.overall_qualification == SignalQualificationStatus.UNQUALIFIED_NOISE

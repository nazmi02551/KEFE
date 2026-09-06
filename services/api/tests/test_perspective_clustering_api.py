from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.clustering_models import PerspectiveArchetype


def test_perspective_clusters_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/perspective-clusters")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["total_arguments_clustered"] == 1000
    assert len(data["clusters"]) == 3

    valid_archetypes = [a.value for a in PerspectiveArchetype]
    total_pct = 0.0
    for cluster in data["clusters"]:
        assert cluster["case_version_id"] == case_id
        assert cluster["archetype"] in valid_archetypes
        assert len(cluster["core_thesis"]) > 0
        assert cluster["argument_count"] > 0
        assert 0.0 <= cluster["support_percentage"] <= 100.0
        total_pct += cluster["support_percentage"]

    assert 99.0 <= total_pct <= 101.0

from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_search_cases_api() -> None:
    app = create_app()
    client = TestClient(app)

    # 1. Search without filters (returns all seeded)
    res = client.get("/v1/discovery/cases/search")
    assert res.status_code == 200
    data = res.json()
    assert data["total_matched"] >= 2
    assert len(data["results"]) >= 2

    # 2. Keyword query matching "Taşıma"
    kw_res = client.get("/v1/discovery/cases/search?q=taşıma")
    assert kw_res.status_code == 200
    kw_data = kw_res.json()
    assert kw_data["total_matched"] == 1
    assert "Toplu Taşıma" in kw_data["results"][0]["title"]

    # 3. Domain filter matching "Technology"
    dom_res = client.get("/v1/discovery/cases/search?domain=Technology")
    assert dom_res.status_code == 200
    dom_data = dom_res.json()
    assert dom_data["total_matched"] == 1
    assert "Yapay Zekâ" in dom_data["results"][0]["title"]

    # 4. Tag filter matching "ulaşım"
    tag_res = client.get("/v1/discovery/cases/search?tags=ulaşım")
    assert tag_res.status_code == 200
    tag_data = tag_res.json()
    assert tag_data["total_matched"] == 1
    assert "ulaşım" in tag_data["results"][0]["tags"]

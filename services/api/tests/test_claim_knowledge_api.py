from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.state.knowledge_repository = InMemoryKnowledgeRepository()
    return TestClient(app)


def test_create_and_get_claim(client: TestClient) -> None:
    create_res = client.post(
        "/v1/claims",
        json={"normalized_text": "Yapay zeka modelleri açık rıza ile eğitilmelidir.", "language_code": "tr"},
    )
    assert create_res.status_code == 201
    created_claim = create_res.json()
    claim_id = created_claim["id"]
    assert created_claim["normalized_text"] == "Yapay zeka modelleri açık rıza ile eğitilmelidir."
    assert created_claim["language_code"] == "tr"
    assert "created_at" in created_claim

    get_res = client.get(f"/v1/claims/{claim_id}")
    assert get_res.status_code == 200
    claim_data = get_res.json()
    assert claim_data["id"] == claim_id
    assert claim_data["assessments"] == []
    assert claim_data["assertions"] == []
    assert claim_data["evidence_links"] == []
    assert claim_data["relations"] == []


def test_get_nonexistent_claim_returns_404(client: TestClient) -> None:
    res = client.get(f"/v1/claims/{uuid4()}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Claim not found"


def test_claim_create_validation(client: TestClient) -> None:
    res = client.post("/v1/claims", json={"normalized_text": "a", "language_code": "tr"})
    assert res.status_code == 422


def test_claim_assessment_lifecycle(client: TestClient) -> None:
    claim_res = client.post(
        "/v1/claims",
        json={"normalized_text": "Su kaynaklarının korunması kamusal bir önceliktir.", "language_code": "tr"},
    )
    claim_id = claim_res.json()["id"]

    # Add first assessment: CLAIMED
    ass1_res = client.post(
        f"/v1/claims/{claim_id}/assessments",
        json={
            "claim_type": "FACTUAL",
            "claim_state": "CLAIMED",
            "taxonomy_version": "v1.0",
            "review_state": "ACCEPTED",
            "reviewer_ref": "editor:alice",
            "rationale_code": "INITIAL_CAPTURE",
        },
    )
    assert ass1_res.status_code == 201
    ass1_data = ass1_res.json()
    assert ass1_data["claim_state"] == "CLAIMED"
    assert ass1_data["claim_type"] == "FACTUAL"

    # Add second assessment: SUPPORTED (append-only lifecycle)
    ass2_res = client.post(
        f"/v1/claims/{claim_id}/assessments",
        json={
            "claim_type": "FACTUAL",
            "claim_state": "SUPPORTED",
            "taxonomy_version": "v1.0",
            "review_state": "ACCEPTED",
            "reviewer_ref": "editor:bob",
            "rationale_code": "EVIDENCE_CONFIRMED",
        },
    )
    assert ass2_res.status_code == 201

    # List assessments
    list_res = client.get(f"/v1/claims/{claim_id}/assessments")
    assert list_res.status_code == 200
    assessments = list_res.json()
    assert len(assessments) == 2
    assert assessments[0]["claim_state"] == "CLAIMED"
    assert assessments[1]["claim_state"] == "SUPPORTED"

    # Full claim retrieval includes assessments
    full_claim = client.get(f"/v1/claims/{claim_id}").json()
    assert len(full_claim["assessments"]) == 2


def test_claim_assessment_for_missing_claim_returns_404(client: TestClient) -> None:
    missing_id = uuid4()
    res = client.post(
        f"/v1/claims/{missing_id}/assessments",
        json={
            "claim_type": "FACTUAL",
            "claim_state": "CLAIMED",
        },
    )
    assert res.status_code == 404

    get_res = client.get(f"/v1/claims/{missing_id}/assessments")
    assert get_res.status_code == 404


def test_claim_assertions(client: TestClient) -> None:
    claim_res = client.post(
        "/v1/claims",
        json={"normalized_text": "Vergi reformu düşük gelirlileri gözetmelidir.", "language_code": "tr"},
    )
    claim_id = claim_res.json()["id"]

    ast_res = client.post(
        f"/v1/claims/{claim_id}/assertions",
        json={
            "claimant_kind": "CIVIL_SOCIETY",
            "claimant_ref": "ngo:economic-justice",
            "provenance_ref": "briefing-doc-12",
        },
    )
    assert ast_res.status_code == 201
    ast_data = ast_res.json()
    assert ast_data["claimant_kind"] == "CIVIL_SOCIETY"
    assert ast_data["claimant_ref"] == "ngo:economic-justice"

    # List assertions
    list_res = client.get(f"/v1/claims/{claim_id}/assertions")
    assert list_res.status_code == 200
    assertions = list_res.json()
    assert len(assertions) == 1
    assert assertions[0]["claimant_ref"] == "ngo:economic-justice"


def test_claim_relations(client: TestClient) -> None:
    c1 = client.post(
        "/v1/claims",
        json={"normalized_text": "Yenilenebilir enerji yatırımları artırılmalıdır.", "language_code": "tr"},
    ).json()["id"]

    c2 = client.post(
        "/v1/claims",
        json={"normalized_text": "Güneş enerjisi panellerine sübvansiyon sağlanmalıdır.", "language_code": "tr"},
    ).json()["id"]

    # Link c2 to c1
    rel_res = client.post(
        f"/v1/claims/{c2}/relations",
        json={
            "to_claim_id": c1,
            "relation_code": "NARROWS_SCOPE_OF",
            "taxonomy_version": "v1.0",
            "review_state": "ACCEPTED",
        },
    )
    assert rel_res.status_code == 201
    rel_data = rel_res.json()
    assert rel_data["from_claim_id"] == c2
    assert rel_data["to_claim_id"] == c1
    assert rel_data["relation_code"] == "NARROWS_SCOPE_OF"

    # Both c1 and c2 should show this relation in their relation list
    r1 = client.get(f"/v1/claims/{c1}/relations").json()
    assert len(r1) == 1
    r2 = client.get(f"/v1/claims/{c2}/relations").json()
    assert len(r2) == 1

    # Self-relation is rejected with 400
    self_rel = client.post(
        f"/v1/claims/{c1}/relations",
        json={
            "to_claim_id": c1,
            "relation_code": "SAME_AS",
        },
    )
    assert self_rel.status_code == 400

    # Non-existent target returns 404
    missing_target = client.post(
        f"/v1/claims/{c1}/relations",
        json={
            "to_claim_id": str(uuid4()),
            "relation_code": "NARROWS_SCOPE_OF",
        },
    )
    assert missing_target.status_code == 404


def test_argument_creation_and_relations(client: TestClient) -> None:
    # Create claim
    claim_id = client.post(
        "/v1/claims",
        json={"normalized_text": "Toplu taşıma ücretleri sübvanse edilmelidir.", "language_code": "tr"},
    ).json()["id"]

    # Create argument
    arg_res = client.post(
        "/v1/arguments",
        json={
            "body": "Düşük gelirli vatandaşların istihdama katılımını artırmak için toplu taşıma erişilebilir olmalıdır.",
            "language_code": "tr",
            "review_state": "ACCEPTED",
            "author_or_claimant_ref": "expert:urban-economist-1",
        },
    )
    assert arg_res.status_code == 201
    arg_data = arg_res.json()
    arg_id = arg_data["id"]
    assert arg_data["review_state"] == "ACCEPTED"

    # Link argument to claim
    arg_rel_res = client.post(
        f"/v1/arguments/{arg_id}/relations",
        json={
            "target_kind": "CLAIM",
            "target_ref": claim_id,
            "relation": "SUPPORTS",
            "taxonomy_version": "v1.0",
            "review_state": "ACCEPTED",
        },
    )
    assert arg_rel_res.status_code == 201
    arg_rel_data = arg_rel_res.json()
    assert arg_rel_data["argument_id"] == arg_id
    assert arg_rel_data["target_kind"] == "CLAIM"
    assert arg_rel_data["target_ref"] == claim_id
    assert arg_rel_data["relation"] == "SUPPORTS"

    # Get argument and verify relations
    get_arg_res = client.get(f"/v1/arguments/{arg_id}")
    assert get_arg_res.status_code == 200
    arg_details = get_arg_res.json()
    assert len(arg_details["relations"]) == 1
    assert arg_details["relations"][0]["relation"] == "SUPPORTS"

    # Argument targeting itself is rejected with 400
    self_arg_rel = client.post(
        f"/v1/arguments/{arg_id}/relations",
        json={
            "target_kind": "ARGUMENT",
            "target_ref": arg_id,
            "relation": "REBUTS",
        },
    )
    assert self_arg_rel.status_code == 400


def test_argument_404(client: TestClient) -> None:
    missing_id = uuid4()
    assert client.get(f"/v1/arguments/{missing_id}").status_code == 404
    assert (
        client.post(
            f"/v1/arguments/{missing_id}/relations",
            json={
                "target_kind": "CLAIM",
                "target_ref": str(uuid4()),
                "relation": "SUPPORTS",
            },
        ).status_code
        == 404
    )
    assert client.get(f"/v1/arguments/{missing_id}/relations").status_code == 404

from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_ai_extract_claims() -> None:
    res = client.post(
        "/v1/editorial/ai/extract-claims",
        json={
            "source_text": "Resmi verilere göre enerji maliyetleri bu yıl yüzde 25 arttı. Belediyeler toplu taşımayı sübvanse etmek zorundadır. Adaletli dağıtım toplum için çok önemlidir.",
            "max_claims": 3,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["extracted_claims"]) > 0
    assert "model_used" in data
    assert "editorial_disclaimer" in data
    first_claim = data["extracted_claims"][0]
    assert first_claim["claim_type"] in ["FACTUAL", "NORMATIVE", "VALUE", "CAUSAL"]
    assert 0.0 <= first_claim["confidence_score"] <= 1.0


def test_ai_suggest_perspectives() -> None:
    res = client.post(
        "/v1/editorial/ai/suggest-perspectives",
        json={
            "dilemma_title": "Şehir İçi Hız Sınırlarının Düşürülmesi",
            "context_summary": "Trafik kazalarını azaltmak için hız sınırının 30 km/s'ye indirilmesi planlanmaktadır.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["perspectives"]) == 3
    orientations = [p["orientation"] for p in data["perspectives"]]
    assert "THESIS" in orientations
    assert "ANTITHESIS" in orientations
    assert "SYNTHESIS_BRIDGE" in orientations


def test_ai_bias_check_flagged() -> None:
    res = client.post(
        "/v1/editorial/ai/bias-check",
        json={
            "content_text": "Alınan bu karar şüphesiz tam bir rezalet ve akılalmaz bir durum yaratmıştır.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_neutral"] is False
    assert data["neutrality_score"] < 1.0
    assert "rezalet" in data["flagged_terms"]
    assert "şüphesiz" in data["flagged_terms"]
    assert "rezalet" in data["suggested_neutral_rephrasings"]


def test_ai_bias_check_clean() -> None:
    res = client.post(
        "/v1/editorial/ai/bias-check",
        json={
            "content_text": "Bakanlık yeni tarifeyi açıkladı ve ilgili tarafların görüşlerini almaya başladı.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_neutral"] is True
    assert data["neutrality_score"] == 1.0
    assert len(data["flagged_terms"]) == 0


def test_ai_compose_summary() -> None:
    raw = (
        "Karayolları Genel Müdürlüğü tarafından yürütülen çalışmalar sonucunda, "
        "kış aylarında meydana gelen buzlanma riskine karşı yeni sensör ağlarının "
        "otoyollara yerleştirilmesi kararlaştırıldı. Bu adım sayesinde kazaların "
        "yüzde kırk oranında önlenmesi hedefleniyor."
    )
    res = client.post(
        "/v1/editorial/ai/compose-summary",
        json={
            "raw_material": raw,
            "target_length_chars": 150,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["composed_summary"]) <= 160
    assert "readability_index" in data

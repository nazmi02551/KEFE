from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.discovery.search_models import (
    SearchableCaseItem,
    SearchFilterQuery,
)
from kefe_api.modules.discovery.search_service import CaseSearchFilterService


def test_case_search_filters_by_keyword_domain_and_tags() -> None:
    now = datetime.now(UTC)
    c1 = SearchableCaseItem(
        case_version_id=uuid4(),
        title="Otonom Araç Kazalarında Sorumluluk Dağılımı",
        summary="Yapay zeka sürücüsüz araç kazalarında üretici ve araç sahibi sorumluluğu.",
        domain="TECH_ETHICS",
        tags=("yapay_zeka", "hukuk", "otonom"),
        status="ACTIVE",
        published_at=now - timedelta(days=2),
    )
    c2 = SearchableCaseItem(
        case_version_id=uuid4(),
        title="Belediye Gece Toplu Taşıma Seferleri",
        summary="Gece saatlerinde ek otobüs seferlerinin kamu bütçesiyle sübvanse edilmesi.",
        domain="MUNICIPAL",
        tags=("ulasim", "kamu_butcesi", "belediye"),
        status="ACTIVE",
        published_at=now - timedelta(days=1),
    )
    c3 = SearchableCaseItem(
        case_version_id=uuid4(),
        title="Tıbbi Yapay Zeka Teşhis Kararları",
        summary="Hayati risk taşıyan teşhislerde hekim ve algoritma mutabakatı.",
        domain="HEALTHCARE",
        tags=("yapay_zeka", "saglik", "etik"),
        status="ARCHIVED",
        published_at=now - timedelta(days=5),
    )

    service = CaseSearchFilterService([c1, c2, c3])

    # 1. Search keyword "yapay zeka"
    res1 = service.search(SearchFilterQuery(keyword="yapay zeka"))
    assert res1.total_matched == 2
    assert {i.domain for i in res1.items} == {"TECH_ETHICS", "HEALTHCARE"}

    # 2. Search domain "MUNICIPAL"
    res2 = service.search(SearchFilterQuery(domain="MUNICIPAL"))
    assert res2.total_matched == 1
    assert res2.items[0].title == "Belediye Gece Toplu Taşıma Seferleri"

    # 3. Search tag "yapay_zeka" + status "ACTIVE"
    res3 = service.search(SearchFilterQuery(tags=("yapay_zeka",), status="ACTIVE"))
    assert res3.total_matched == 1
    assert res3.items[0].domain == "TECH_ETHICS"

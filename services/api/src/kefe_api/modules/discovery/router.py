from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from kefe_api.modules.discovery.search_models import (
    SearchableCaseItem,
    SearchFilterQuery,
)
from kefe_api.modules.discovery.search_service import CaseSearchFilterService

discovery_router = APIRouter(prefix="/v1/discovery", tags=["Discovery"])

_DEFAULT_SEARCH_SERVICE = CaseSearchFilterService(
    [
        SearchableCaseItem(
            case_version_id=UUID("22222222-2222-4222-8222-222222222222"),
            title="Toplu Taşıma Öncelik İkilemi",
            summary="Metro ve otobüslerde yaşlı, engelli ve hamile yolculara yer verme zorunluluğunun sınırları.",
            domain="Civic",
            tags=("ulaşım", "etik", "kamusal-alan"),
            status="PUBLISHED",
            published_at=datetime(2026, 8, 20, 10, 0, tzinfo=UTC),
        ),
        SearchableCaseItem(
            case_version_id=UUID("22222222-2222-4222-8222-222222222223"),
            title="Yapay Zekâ ve Veri Mahremiyeti",
            summary="Kamu hizmetlerinde yapay zekâ modellerinin vatandaş verisiyle eğitilmesinin meşruiyeti.",
            domain="Technology",
            tags=("yapay-zeka", "mahremiyet", "veri"),
            status="PUBLISHED",
            published_at=datetime(2026, 8, 25, 14, 30, tzinfo=UTC),
        ),
    ]
)


def get_search_service() -> CaseSearchFilterService:
    return _DEFAULT_SEARCH_SERVICE


class SearchResultItemOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_version_id: UUID
    title: str
    summary: str
    domain: str
    tags: list[str]
    status: str
    published_at: datetime


class SearchFilterResultOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    selected_domain: str | None
    selected_tags: list[str]
    total_matched: int
    results: list[SearchResultItemOut]


@discovery_router.get(
    "/cases/search",
    response_model=SearchFilterResultOut,
)
def search_cases(
    q: Annotated[str | None, Query(description="Search keyword")] = None,
    domain: Annotated[str | None, Query(description="Domain filter")] = None,
    tags: Annotated[
        str | None, Query(description="Comma-separated tags")
    ] = None,
    status: Annotated[str | None, Query(description="Case status")] = None,
    service: CaseSearchFilterService = Depends(get_search_service),
) -> SearchFilterResultOut:
    tag_tuple: tuple[str, ...] = ()
    if tags:
        tag_tuple = tuple(t.strip() for t in tags.split(",") if t.strip())

    filter_query = SearchFilterQuery(
        keyword=q,
        domain=domain,
        tags=tag_tuple,
        status=status,
    )

    result = service.search(filter_query)

    return SearchFilterResultOut(
        query=q or "",
        selected_domain=domain,
        selected_tags=list(tag_tuple),
        total_matched=result.total_matched,
        results=[
            SearchResultItemOut(
                case_version_id=item.case_version_id,
                title=item.title,
                summary=item.summary,
                domain=item.domain,
                tags=list(item.tags),
                status=item.status,
                published_at=item.published_at,
            )
            for item in result.items
        ],
    )


from kefe_api.modules.discovery.user_discovery_profile import (
    ComplexityLevel,
    DomainPreference,
    FreshnessPreference,
    RealEventPreference,
    UserDiscoveryProfileService,
)

_DEFAULT_PROFILE_SERVICE = UserDiscoveryProfileService()


class UserDiscoveryProfileOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    preferred_domains: list[str]
    complexity_level: str
    freshness_preference: str
    real_event_preference: str
    diversification_boost: float
    updated_at: datetime


class UserDiscoveryProfileUpdateIn(BaseModel):
    preferred_domains: list[str]
    complexity_level: str
    freshness_preference: str
    real_event_preference: str
    diversification_boost: float


@discovery_router.get(
    "/profile",
    response_model=UserDiscoveryProfileOut,
)
def get_user_discovery_profile(
    user_id: str = Query(default="guest-current-actor", description="User or anonymous actor ID"),
) -> UserDiscoveryProfileOut:
    profile = _DEFAULT_PROFILE_SERVICE.get_profile(user_id)
    return UserDiscoveryProfileOut(
        user_id=profile.user_id,
        preferred_domains=[d.value for d in profile.preferred_domains],
        complexity_level=profile.complexity_level.value,
        freshness_preference=profile.freshness_preference.value,
        real_event_preference=profile.real_event_preference.value,
        diversification_boost=profile.diversification_boost,
        updated_at=profile.updated_at,
    )


@discovery_router.put(
    "/profile",
    response_model=UserDiscoveryProfileOut,
)
def update_user_discovery_profile(
    body: UserDiscoveryProfileUpdateIn,
    user_id: str = Query(default="guest-current-actor", description="User or anonymous actor ID"),
) -> UserDiscoveryProfileOut:
    domains = [
        DomainPreference(d.upper())
        for d in body.preferred_domains
        if d.upper() in DomainPreference.__members__
    ]
    if not domains:
        domains = [DomainPreference.CIVIC]

    complexity = (
        ComplexityLevel(body.complexity_level.upper())
        if body.complexity_level.upper() in ComplexityLevel.__members__
        else ComplexityLevel.BALANCED
    )
    freshness = (
        FreshnessPreference(body.freshness_preference.upper())
        if body.freshness_preference.upper() in FreshnessPreference.__members__
        else FreshnessPreference.BALANCED
    )
    real_event = (
        RealEventPreference(body.real_event_preference.upper())
        if body.real_event_preference.upper() in RealEventPreference.__members__
        else RealEventPreference.BALANCED
    )

    profile = _DEFAULT_PROFILE_SERVICE.update_profile(
        user_id=user_id,
        preferred_domains=domains,
        complexity_level=complexity,
        freshness_preference=freshness,
        real_event_preference=real_event,
        diversification_boost=body.diversification_boost,
    )

    return UserDiscoveryProfileOut(
        user_id=profile.user_id,
        preferred_domains=[d.value for d in profile.preferred_domains],
        complexity_level=profile.complexity_level.value,
        freshness_preference=profile.freshness_preference.value,
        real_event_preference=profile.real_event_preference.value,
        diversification_boost=profile.diversification_boost,
        updated_at=profile.updated_at,
    )


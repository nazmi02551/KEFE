from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from kefe_api.modules.discovery.search_models import (
    SearchableCaseItem,
    SearchFilterQuery,
    SearchFilterResult,
)


class CaseSearchFilterService:
    def __init__(self, cases: Iterable[SearchableCaseItem] | None = None) -> None:
        self._cases_by_id: dict[UUID, SearchableCaseItem] = {
            c.case_version_id: c for c in (cases or [])
        }

    def register_case(self, case_item: SearchableCaseItem) -> None:
        self._cases_by_id[case_item.case_version_id] = case_item

    def search(self, query: SearchFilterQuery) -> SearchFilterResult:
        matched: list[SearchableCaseItem] = []
        kw = (query.keyword or "").strip().lower()

        for case_item in self._cases_by_id.values():
            if query.domain and case_item.domain.lower() != query.domain.strip().lower():
                continue

            if query.status and case_item.status.lower() != query.status.strip().lower():
                continue

            if query.tags:
                tag_set = {t.lower() for t in case_item.tags}
                required_tags = {t.lower() for t in query.tags}
                if not required_tags.issubset(tag_set):
                    continue

            if kw:
                title_match = kw in case_item.title.lower()
                summary_match = kw in case_item.summary.lower()
                tag_match = any(kw in t.lower() for t in case_item.tags)
                if not (title_match or summary_match or tag_match):
                    continue

            matched.append(case_item)

        # Deterministic sort by published_at descending
        matched.sort(key=lambda c: c.published_at, reverse=True)

        return SearchFilterResult(
            query=query,
            total_matched=len(matched),
            items=tuple(matched),
        )

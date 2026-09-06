from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SearchableCaseItem:
    case_version_id: UUID
    title: str
    summary: str
    domain: str
    tags: tuple[str, ...]
    status: str
    published_at: datetime


@dataclass(frozen=True, slots=True)
class SearchFilterQuery:
    keyword: str | None = None
    domain: str | None = None
    tags: tuple[str, ...] = ()
    status: str | None = None


@dataclass(frozen=True, slots=True)
class SearchFilterResult:
    query: SearchFilterQuery
    total_matched: int
    items: tuple[SearchableCaseItem, ...]

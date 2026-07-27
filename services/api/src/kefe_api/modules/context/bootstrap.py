from __future__ import annotations

from uuid import UUID

from kefe_api.modules.context.in_memory import InMemoryContextRepository
from kefe_api.modules.context.models import (
    ClaimStatus,
    ContextBlock,
    ContextSnapshot,
    ContextSource,
    DisclosureLevel,
    SourceKind,
)
from kefe_api.modules.decision.bootstrap import DEMO_CASE_VERSION_ID

DEMO_CONTEXT_BLOCK_ID = UUID("91000000-0000-4000-8000-000000000001")
DEMO_CONTEXT_DETAIL_ID = UUID("91000000-0000-4000-8000-000000000002")
DEMO_CONTEXT_SOURCE_ID = UUID("92000000-0000-4000-8000-000000000001")


def build_demo_context_repository() -> InMemoryContextRepository:
    source = ContextSource(
        id=DEMO_CONTEXT_SOURCE_ID,
        case_version_id=DEMO_CASE_VERSION_ID,
        title="KEFE Demo Senaryo Notu",
        publisher="KEFE Editorial",
        source_kind=SourceKind.EDITORIAL,
    )
    snapshot = ContextSnapshot(
        case_version_id=DEMO_CASE_VERSION_ID,
        blocks=(
            ContextBlock(
                id=DEMO_CONTEXT_BLOCK_ID,
                case_version_id=DEMO_CASE_VERSION_ID,
                display_order=0,
                disclosure_level=DisclosureLevel.ESSENTIAL,
                title="Durum",
                body=(
                    "Toplu taşımada yalnız bir boş koltuk vardır ve iki kişinin de makul "
                    "bir öncelik gerekçesi bulunmaktadır."
                ),
                claim_status=ClaimStatus.VERIFIED,
                source_ids=(DEMO_CONTEXT_SOURCE_ID,),
            ),
            ContextBlock(
                id=DEMO_CONTEXT_DETAIL_ID,
                case_version_id=DEMO_CASE_VERSION_ID,
                display_order=10,
                disclosure_level=DisclosureLevel.DETAIL,
                title="Tartılması gereken çatışma",
                body=(
                    "Karar, görünür ihtiyaç ile sırayı ve eşit uygulamayı koruma arasında "
                    "bir öncelik çatışması oluşturur."
                ),
                claim_status=ClaimStatus.UNKNOWN,
                source_ids=(DEMO_CONTEXT_SOURCE_ID,),
            ),
        ),
        sources=(source,),
    )
    return InMemoryContextRepository([snapshot])

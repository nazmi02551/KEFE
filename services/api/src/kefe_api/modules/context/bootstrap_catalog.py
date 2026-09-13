# bootstrap_catalog.py — context
# Generates InMemoryContextRepository snapshots from beta_catalog.py
# for all catalog cases, enabling context screens in InMemory (no-postgres) mode.
from __future__ import annotations

from uuid import UUID, uuid5

from kefe_api.infrastructure.beta_catalog import BETA_CATALOG, CATALOG_NAMESPACE
from kefe_api.modules.context.in_memory import InMemoryContextRepository
from kefe_api.modules.context.models import (
    ClaimStatus,
    ContextBlock,
    ContextSnapshot,
    ContextSource,
    DisclosureLevel,
    SourceKind,
)

_DISCLOSURE_MAP = {
    "ESSENTIAL": DisclosureLevel.ESSENTIAL,
    "DETAIL": DisclosureLevel.DETAIL,
    "DATA_POINT": DisclosureLevel.DETAIL,  # DATA_POINT renders as DETAIL
}


def build_catalog_context_repository() -> InMemoryContextRepository:
    snapshots: list[ContextSnapshot] = []

    for item in BETA_CATALOG:
        source_id = uuid5(CATALOG_NAMESPACE, f"context_source:{item.slug}:editorial")
        source = ContextSource(
            id=source_id,
            case_version_id=item.version_id,
            title="KEFE Beta Editoryal Senaryo Notu",
            publisher="KEFE Editorial",
            source_kind=SourceKind.EDITORIAL,
        )

        blocks: list[ContextBlock] = []

        if item.context_blocks:
            for idx, ctx in enumerate(item.context_blocks):
                block_id = uuid5(
                    CATALOG_NAMESPACE,
                    f"context_block:{item.slug}:{ctx.block_type}:{idx}",
                )
                disclosure = _DISCLOSURE_MAP.get(ctx.block_type, DisclosureLevel.DETAIL)
                blocks.append(
                    ContextBlock(
                        id=block_id,
                        case_version_id=item.version_id,
                        display_order=idx * 10,
                        disclosure_level=disclosure,
                        title=ctx.label,
                        body=ctx.body,
                        claim_status=ClaimStatus.CLAIMED,
                        source_ids=(source_id,),
                    )
                )
        else:
            # Minimal fallback block so the context screen is never empty
            fallback_id = uuid5(CATALOG_NAMESPACE, f"context_block:{item.slug}:fallback")
            blocks.append(
                ContextBlock(
                    id=fallback_id,
                    case_version_id=item.version_id,
                    display_order=0,
                    disclosure_level=DisclosureLevel.ESSENTIAL,
                    title="Durum",
                    body=item.summary,
                    claim_status=ClaimStatus.CLAIMED,
                    source_ids=(source_id,),
                )
            )

        snapshots.append(
            ContextSnapshot(
                case_version_id=item.version_id,
                blocks=tuple(blocks),
                sources=(source,),
            )
        )

    return InMemoryContextRepository(snapshots)
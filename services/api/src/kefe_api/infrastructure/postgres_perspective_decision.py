from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_reason_decision import PostgresReasonDecisionRepository
from kefe_api.modules.decision.models import (
    PerspectiveCard,
    PerspectiveMode,
    PerspectiveSlot,
    PerspectiveSnapshot,
    PerspectiveSourceKind,
    ReasonModerationState,
)


class PostgresPerspectiveDecisionRepository(PostgresReasonDecisionRepository):
    """Decision adapter including the bounded curated Perspective read model."""

    def get_perspective(self, case_version_id: UUID) -> PerspectiveSnapshot | None:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        id,
                        slot,
                        body,
                        source_kind,
                        provenance_label,
                        moderation_state,
                        published_at
                    FROM content.perspective_card
                    WHERE case_version_id = :case_version_id
                      AND status = 'PUBLISHED'
                    ORDER BY
                        CASE slot
                            WHEN 'NEAR' THEN 1
                            WHEN 'OPPOSING' THEN 2
                            WHEN 'BRIDGE' THEN 3
                            WHEN 'ALTERNATIVE_CONTEXT' THEN 4
                        END,
                        id
                    LIMIT 4
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()

        if not rows:
            return None

        cards = tuple(
            PerspectiveCard(
                perspective_id=row["id"],
                slot=PerspectiveSlot(row["slot"]),
                body=row["body"],
                source_kind=PerspectiveSourceKind(row["source_kind"]),
                provenance_label=row["provenance_label"],
                moderation_state=ReasonModerationState(row["moderation_state"]),
            )
            for row in rows
        )
        return PerspectiveSnapshot(
            case_version_id=case_version_id,
            mode=PerspectiveMode.DEGRADED_CURATED,
            sample_kind="CURATED_FALLBACK",
            sample_size=len(cards),
            generated_at=max(row["published_at"] for row in rows) or datetime.now(UTC),
            provenance_note="Published KEFE editorial cards; no community reasons included.",
            cards=cards,
        )

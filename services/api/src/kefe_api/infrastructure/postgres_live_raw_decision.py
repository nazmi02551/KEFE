from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_explore_decision import (
    PostgresExploreDecisionRepository,
)
from kefe_api.modules.decision.models import RevealSnapshot


class PostgresLiveRawDecisionRepository(PostgresExploreDecisionRepository):
    """Adds a bounded live RAW Collective Result fallback for Connected Alpha.

    Reviewed TRUSTED snapshots remain authoritative when present. RAW is derived only when a
    CaseVersion has no TRUSTED snapshot, and only from committed SINGLE_CHOICE decision
    responses. It is observed population data, not Signal/Impact or a representativeness claim.
    """

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None:
        trusted = super().get_reveal(case_version_id)
        if trusted is not None:
            return trusted

        with self._engine.connect() as connection:
            decision_question = (
                connection.execute(
                    text(
                        """
                        SELECT qv.id, qv.response_schema
                        FROM content.issue i
                        JOIN content.question q ON q.issue_id = i.id
                        JOIN LATERAL (
                            SELECT
                                version.id,
                                version.response_type,
                                version.response_schema,
                                version.is_required
                            FROM content.question_version version
                            WHERE version.question_id = q.id
                              AND version.is_active = true
                            ORDER BY version.version_no DESC
                            LIMIT 1
                        ) qv ON true
                        WHERE i.case_version_id = :case_version_id
                          AND qv.response_type = 'SINGLE_CHOICE'
                          AND qv.is_required = true
                        ORDER BY i.sort_order, q.sort_order, q.id
                        LIMIT 1
                        """
                    ),
                    {"case_version_id": case_version_id},
                )
                .mappings()
                .one_or_none()
            )
            if decision_question is None:
                return None

            raw_options = (decision_question["response_schema"] or {}).get("options", [])
            options = tuple(
                dict.fromkeys(
                    str(option)
                    for option in raw_options
                    if isinstance(option, str) and option
                )
            )
            if not options:
                return None

            rows = (
                connection.execute(
                    text(
                        """
                        SELECT
                            r.value_json #>> '{}' AS option_code,
                            count(*) AS option_count
                        FROM decision.weigh_session ws
                        JOIN decision.response r ON r.session_id = ws.id
                        WHERE ws.case_version_id = :case_version_id
                          AND ws.state = 'COMMITTED'
                          AND r.question_version_id = :question_version_id
                        GROUP BY r.value_json #>> '{}'
                        """
                    ),
                    {
                        "case_version_id": case_version_id,
                        "question_version_id": decision_question["id"],
                    },
                )
                .mappings()
                .all()
            )

        configured = set(options)
        counts = {
            row["option_code"]: int(row["option_count"])
            for row in rows
            if row["option_code"] in configured
        }
        sample_size = sum(counts.values())
        if sample_size == 0:
            return None

        return RevealSnapshot(
            case_version_id=case_version_id,
            layer="RAW",
            n=sample_size,
            confidence="INSUFFICIENT",
            generated_at=datetime.now(UTC),
            payload={
                option: counts.get(option, 0) / sample_size
                for option in options
            },
        )

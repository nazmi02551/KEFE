from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus
from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)


class PostgresImpactRepository:
    """PostgreSQL-backed implementation of ImpactRepository.

    Schema lives in the ``impact`` schema (migration 20260910_0042).

    Invariants:
    - institution_response rows are insert-only; no UPDATE or DELETE.
    - action_milestone rows are inserted on save_action() and replaced on update_action().
    - list_verified_responses() filters by verification_status = 'VERIFIED'.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Institution Responses
    # ------------------------------------------------------------------

    def save_institution_response(self, response: InstitutionResponse) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO impact.institution_response (
                        response_id,
                        case_version_id,
                        institution_name,
                        authority_role,
                        verification_status,
                        response_type,
                        statement,
                        published_at,
                        milestone_date
                    ) VALUES (
                        :response_id,
                        :case_version_id,
                        :institution_name,
                        :authority_role,
                        :verification_status,
                        :response_type,
                        :statement,
                        :published_at,
                        :milestone_date
                    )
                    ON CONFLICT (response_id) DO NOTHING
                    """
                ),
                {
                    "response_id": response.response_id,
                    "case_version_id": response.case_version_id,
                    "institution_name": response.institution_name,
                    "authority_role": response.authority_role,
                    "verification_status": response.verification_status.value,
                    "response_type": response.response_type.value,
                    "statement": response.statement,
                    "published_at": response.published_at,
                    "milestone_date": response.milestone_date,
                },
            )

    def get_institution_response(self, response_id: UUID) -> InstitutionResponse | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        response_id, case_version_id, institution_name,
                        authority_role, verification_status, response_type,
                        statement, published_at, milestone_date
                    FROM impact.institution_response
                    WHERE response_id = :response_id
                    """
                ),
                {"response_id": response_id},
            ).mappings().one_or_none()
        return None if row is None else self._row_to_response(row)

    def list_verified_responses(self, case_version_id: UUID) -> list[InstitutionResponse]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        response_id, case_version_id, institution_name,
                        authority_role, verification_status, response_type,
                        statement, published_at, milestone_date
                    FROM impact.institution_response
                    WHERE case_version_id     = :case_version_id
                      AND verification_status = 'VERIFIED'
                    ORDER BY published_at DESC
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()
        return [self._row_to_response(r) for r in rows]

    def list_all_responses(
        self,
        *,
        case_version_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InstitutionResponse]:
        if case_version_id is not None:
            sql = """
                SELECT
                    response_id, case_version_id, institution_name,
                    authority_role, verification_status, response_type,
                    statement, published_at, milestone_date
                FROM impact.institution_response
                WHERE case_version_id = :case_version_id
                ORDER BY published_at DESC
                LIMIT :limit OFFSET :offset
            """
            params: dict = {
                "case_version_id": case_version_id,
                "limit": limit,
                "offset": offset,
            }
        else:
            sql = """
                SELECT
                    response_id, case_version_id, institution_name,
                    authority_role, verification_status, response_type,
                    statement, published_at, milestone_date
                FROM impact.institution_response
                ORDER BY published_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"limit": limit, "offset": offset}

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        return [self._row_to_response(r) for r in rows]

    # ------------------------------------------------------------------
    # Action Milestones
    # ------------------------------------------------------------------

    def save_action(self, action: ActionMilestone) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO impact.action_milestone (
                        action_id,
                        case_version_id,
                        title,
                        description,
                        status,
                        progress_percentage,
                        institution_response_id,
                        target_completion_date,
                        evidence_summary,
                        evidence_url,
                        created_at
                    ) VALUES (
                        :action_id,
                        :case_version_id,
                        :title,
                        :description,
                        :status,
                        :progress_percentage,
                        :institution_response_id,
                        :target_completion_date,
                        :evidence_summary,
                        :evidence_url,
                        :created_at
                    )
                    ON CONFLICT (action_id) DO NOTHING
                    """
                ),
                self._action_params(action),
            )

    def get_action(self, action_id: UUID) -> ActionMilestone | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        action_id, case_version_id, title, description,
                        status, progress_percentage, institution_response_id,
                        target_completion_date, evidence_summary, evidence_url,
                        created_at
                    FROM impact.action_milestone
                    WHERE action_id = :action_id
                    """
                ),
                {"action_id": action_id},
            ).mappings().one_or_none()
        return None if row is None else self._row_to_action(row)

    def update_action(self, action: ActionMilestone) -> None:
        with self._engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE impact.action_milestone SET
                        title                   = :title,
                        description             = :description,
                        status                  = :status,
                        progress_percentage     = :progress_percentage,
                        institution_response_id = :institution_response_id,
                        target_completion_date  = :target_completion_date,
                        evidence_summary        = :evidence_summary,
                        evidence_url            = :evidence_url,
                        updated_at              = now()
                    WHERE action_id = :action_id
                    """
                ),
                self._action_params(action),
            )
            if result.rowcount == 0:
                raise KeyError(f"Action {action.action_id} not found")

    def list_actions(
        self,
        case_version_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        action_id, case_version_id, title, description,
                        status, progress_percentage, institution_response_id,
                        target_completion_date, evidence_summary, evidence_url,
                        created_at
                    FROM impact.action_milestone
                    WHERE case_version_id = :case_version_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"case_version_id": case_version_id, "limit": limit, "offset": offset},
            ).mappings().all()
        return [self._row_to_action(r) for r in rows]

    def list_all_actions(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        action_id, case_version_id, title, description,
                        status, progress_percentage, institution_response_id,
                        target_completion_date, evidence_summary, evidence_url,
                        created_at
                    FROM impact.action_milestone
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": limit, "offset": offset},
            ).mappings().all()
        return [self._row_to_action(r) for r in rows]

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_response(row) -> InstitutionResponse:
        return InstitutionResponse(
            response_id=row["response_id"],
            case_version_id=row["case_version_id"],
            institution_name=row["institution_name"],
            authority_role=row["authority_role"],
            verification_status=AuthorityVerificationStatus(row["verification_status"]),
            response_type=InstitutionResponseType(row["response_type"]),
            statement=row["statement"],
            published_at=row["published_at"],
            milestone_date=row["milestone_date"],
        )

    @staticmethod
    def _row_to_action(row) -> ActionMilestone:
        return ActionMilestone(
            action_id=row["action_id"],
            case_version_id=row["case_version_id"],
            title=row["title"],
            description=row["description"],
            status=ActionStatus(row["status"]),
            progress_percentage=int(row["progress_percentage"]),
            institution_response_id=row["institution_response_id"],
            target_completion_date=row["target_completion_date"],
            evidence_summary=row["evidence_summary"],
            evidence_url=row["evidence_url"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _action_params(action: ActionMilestone) -> dict:
        return {
            "action_id": action.action_id,
            "case_version_id": action.case_version_id,
            "title": action.title,
            "description": action.description,
            "status": action.status.value,
            "progress_percentage": action.progress_percentage,
            "institution_response_id": action.institution_response_id,
            "target_completion_date": action.target_completion_date,
            "evidence_summary": action.evidence_summary,
            "evidence_url": action.evidence_url,
            "created_at": action.created_at,
        }
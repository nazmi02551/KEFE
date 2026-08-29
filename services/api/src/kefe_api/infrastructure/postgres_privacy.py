from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, bindparam, text

from kefe_api.modules.privacy.models import PrivacyDeletionReceipt


class PostgresPrivacyRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def export_actor_data(self, actor_id: UUID) -> dict[str, object]:
        with self._engine.connect() as connection:
            sessions = (
                connection.execute(
                    text(
                        """
                    SELECT id, case_id, case_version_id, state, started_at, committed_at
                    FROM decision.weigh_session
                    WHERE actor_id = :actor_id
                    ORDER BY started_at ASC, id ASC
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .all()
            )
            session_ids = [row["id"] for row in sessions]
            responses = []
            reasons = []
            revisions = []
            if session_ids:
                stmt = text(
                    """
                    SELECT session_id, question_version_id, value_json, updated_at
                    FROM decision.response
                    WHERE session_id IN :session_ids
                    ORDER BY session_id, question_version_id
                    """
                ).bindparams(bindparam("session_ids", expanding=True))
                responses = connection.execute(stmt, {"session_ids": session_ids}).mappings().all()
                stmt = text(
                    """
                    SELECT session_id, tags, text_body AS text, moderation_state, updated_at
                    FROM decision.private_reason
                    WHERE session_id IN :session_ids
                    ORDER BY session_id
                    """
                ).bindparams(bindparam("session_ids", expanding=True))
                reasons = connection.execute(stmt, {"session_ids": session_ids}).mappings().all()
                revisions = (
                    connection.execute(
                        text(
                            """
                        SELECT id, session_id, revision_no, flow_step_code,
                               contribution_class, committed_at
                        FROM decision.decision_revision
                        WHERE actor_id = :actor_id
                        ORDER BY committed_at ASC, revision_no ASC, id ASC
                        """
                        ),
                        {"actor_id": actor_id},
                    )
                    .mappings()
                    .all()
                )
            community = (
                connection.execute(
                    text(
                        """
                    SELECT id, case_version_id, tags, body, moderation_state, created_at
                    FROM community.reason
                    WHERE actor_id = :actor_id
                    ORDER BY created_at ASC, id ASC
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .all()
            )
            shares = (
                connection.execute(
                    text(
                        """
                    SELECT id, case_id, case_version_id, include_decision, created_at,
                           expires_at, revoked_at
                    FROM sharing.share_record
                    WHERE actor_id = :actor_id
                    ORDER BY created_at ASC, id ASC
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .all()
            )
            consensus = (
                connection.execute(
                    text(
                        """
                    SELECT card_version_id, case_version_id, stance_code, reason_tag_codes,
                           contribution_class, participated_at
                    FROM collective.consensus_participation
                    WHERE actor_id = :actor_id
                    ORDER BY participated_at ASC, card_version_id ASC
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .all()
            )

        response_map: dict[UUID, list[dict[str, object]]] = {}
        for row in responses:
            response_map.setdefault(row["session_id"], []).append(
                {
                    "question_version_id": str(row["question_version_id"]),
                    "value": row["value_json"],
                    "updated_at": row["updated_at"].isoformat(),
                }
            )
        reason_map = {
            row["session_id"]: {
                "tags": list(row["tags"]),
                "text": row["text"],
                "moderation_state": row["moderation_state"],
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in reasons
        }
        return {
            "weigh_sessions": [
                {
                    "session_id": str(row["id"]),
                    "case_id": str(row["case_id"]),
                    "case_version_id": str(row["case_version_id"]),
                    "state": row["state"],
                    "started_at": row["started_at"].isoformat(),
                    "committed_at": (
                        row["committed_at"].isoformat() if row["committed_at"] else None
                    ),
                    "responses": response_map.get(row["id"], []),
                    "private_reason": reason_map.get(row["id"]),
                }
                for row in sessions
            ],
            "private_reasons": [
                {
                    "session_id": str(row["session_id"]),
                    "tags": list(row["tags"]),
                    "text": row["text"],
                    "moderation_state": row["moderation_state"],
                    "updated_at": row["updated_at"].isoformat(),
                }
                for row in reasons
            ],
            "decision_revisions": [
                {
                    "revision_id": str(row["id"]),
                    "session_id": str(row["session_id"]),
                    "revision_no": row["revision_no"],
                    "flow_step_code": row["flow_step_code"],
                    "contribution_class": row["contribution_class"],
                    "committed_at": row["committed_at"].isoformat(),
                }
                for row in revisions
            ],
            "community_reasons": [
                {
                    "reason_id": str(row["id"]),
                    "case_version_id": str(row["case_version_id"]),
                    "tags": list(row["tags"]),
                    "text": row["body"],
                    "moderation_state": row["moderation_state"],
                    "created_at": row["created_at"].isoformat(),
                }
                for row in community
            ],
            "shares": [
                {
                    "share_id": str(row["id"]),
                    "case_id": str(row["case_id"]),
                    "case_version_id": str(row["case_version_id"]),
                    "include_decision": row["include_decision"],
                    "created_at": row["created_at"].isoformat(),
                    "expires_at": row["expires_at"].isoformat(),
                    "revoked_at": (row["revoked_at"].isoformat() if row["revoked_at"] else None),
                }
                for row in shares
            ],
            "consensus_participations": [
                {
                    "card_version_id": str(row["card_version_id"]),
                    "case_version_id": str(row["case_version_id"]),
                    "stance_code": row["stance_code"],
                    "reason_tag_codes": list(row["reason_tag_codes"]),
                    "contribution_class": row["contribution_class"],
                    "participated_at": row["participated_at"].isoformat(),
                }
                for row in consensus
            ],
        }

    def delete_actor_data(
        self,
        *,
        actor_id: UUID,
        actor_kind: str,
        deleted_at: datetime,
    ) -> PrivacyDeletionReceipt:
        with self._engine.begin() as connection:
            actor = (
                connection.execute(
                    text(
                        """
                    SELECT actor_kind, state
                    FROM identity.actor
                    WHERE id = :actor_id
                    FOR UPDATE
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .one_or_none()
            )
            existing = (
                connection.execute(
                    text(
                        """
                    SELECT id, actor_id, actor_kind, deleted_at,
                           private_data_deleted, aggregate_contributions_anonymized,
                           policy_version
                    FROM privacy.actor_deletion_receipt
                    WHERE actor_id = :actor_id
                    """
                    ),
                    {"actor_id": actor_id},
                )
                .mappings()
                .one_or_none()
            )
            self._anonymize_analytics_actor(connection, actor_id)
            if existing is not None:
                return self._receipt(existing)
            if actor is None:
                raise ValueError("privacy deletion actor was not found")
            if actor["actor_kind"] != actor_kind:
                raise ValueError("privacy deletion actor kind conflict")

            receipt_id = uuid4()
            session_ids = (
                connection.execute(
                    text("SELECT id FROM decision.weigh_session WHERE actor_id = :actor_id"),
                    {"actor_id": actor_id},
                )
                .scalars()
                .all()
            )
            identifier_hashes = (
                connection.execute(
                    text(
                        "SELECT identifier_hash FROM identity.account_identifier WHERE actor_id = :actor_id"
                    ),
                    {"actor_id": actor_id},
                )
                .scalars()
                .all()
            )

            if session_ids:
                stmt = text(
                    """
                    UPDATE analytics.outbox_event
                    SET payload = (payload - 'actor_id')
                        || jsonb_build_object('actor_deleted', true)
                    WHERE aggregate_id IN :session_ids
                    """
                ).bindparams(bindparam("session_ids", expanding=True))
                connection.execute(stmt, {"session_ids": session_ids})

            connection.execute(
                text(
                    """
                    UPDATE decision.weigh_session
                    SET merged_from_actor_id = NULL
                    WHERE merged_from_actor_id = :actor_id
                      AND actor_id <> :actor_id
                    """
                ),
                {"actor_id": actor_id},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM identity.actor_merge
                    WHERE guest_actor_id = :actor_id OR account_actor_id = :actor_id
                    """
                ),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM sharing.share_record WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM community.reason_reaction WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM community.reason_report WHERE reporter_actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM community.reason WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM collective.consensus_participation WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM decision.weigh_session WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM identity.actor_session WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text("DELETE FROM identity.account_identifier WHERE actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
            if identifier_hashes:
                challenge_stmt = text(
                    "DELETE FROM identity.otp_challenge WHERE identifier_hash IN :hashes"
                ).bindparams(bindparam("hashes", expanding=True))
                connection.execute(challenge_stmt, {"hashes": identifier_hashes})
                verification_stmt = text(
                    "DELETE FROM identity.otp_verification WHERE identifier_hash IN :hashes"
                ).bindparams(bindparam("hashes", expanding=True))
                connection.execute(verification_stmt, {"hashes": identifier_hashes})
            connection.execute(
                text("UPDATE identity.actor SET state = 'DELETED' WHERE id = :actor_id"),
                {"actor_id": actor_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO privacy.actor_deletion_receipt (
                        id, actor_id, actor_kind, deleted_at, private_data_deleted,
                        aggregate_contributions_anonymized, policy_version
                    ) VALUES (
                        :id, :actor_id, :actor_kind, :deleted_at,
                        true, true, 'PRIVACY_SELF_SERVICE_V2'
                    )
                    """
                ),
                {
                    "id": receipt_id,
                    "actor_id": actor_id,
                    "actor_kind": actor["actor_kind"],
                    "deleted_at": deleted_at,
                },
            )
            return PrivacyDeletionReceipt(
                receipt_id=receipt_id,
                actor_id=actor_id,
                actor_kind=actor["actor_kind"],
                deleted_at=deleted_at,
                private_data_deleted=True,
                aggregate_contributions_anonymized=True,
                policy_version="PRIVACY_SELF_SERVICE_V2",
            )

    @staticmethod
    def _anonymize_analytics_actor(connection, actor_id: UUID) -> None:
        connection.execute(
            text(
                "UPDATE analytics.analytics_event "
                "SET actor_id = NULL WHERE actor_id = :actor_id"
            ),
            {"actor_id": actor_id},
        )
        connection.execute(
            text(
                "UPDATE analytics.activation_journey "
                "SET actor_id = NULL WHERE actor_id = :actor_id"
            ),
            {"actor_id": actor_id},
        )

    @staticmethod
    def _receipt(row: object) -> PrivacyDeletionReceipt:
        return PrivacyDeletionReceipt(
            receipt_id=row["id"],
            actor_id=row["actor_id"],
            actor_kind=row["actor_kind"],
            deleted_at=row["deleted_at"],
            private_data_deleted=row["private_data_deleted"],
            aggregate_contributions_anonymized=row["aggregate_contributions_anonymized"],
            policy_version=row["policy_version"],
        )

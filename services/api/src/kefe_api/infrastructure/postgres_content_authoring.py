from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringContextBlock,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)


class PostgresContentAuthoringRepository:
    """Durable editorial adapter; consumer rows are materialized only on publication."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_case(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
    ) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.case_item (id, slug, created_at)
                        VALUES (:id, :slug, :created_at)
                        """
                    ),
                    {
                        "id": identity.id,
                        "slug": identity.slug,
                        "created_at": identity.created_at,
                    },
                )
                self._insert_version(connection, initial_version)
                self._insert_audit(connection, audit)
        except IntegrityError as exc:
            raise ValueError("case or initial version already exists") from exc

    def get_case(self, case_id: UUID) -> CaseIdentity | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, slug, created_at
                    FROM editorial.case_item
                    WHERE id = :case_id
                    """
                ),
                {"case_id": case_id},
            ).mappings().one_or_none()
        if row is None:
            return None
        return CaseIdentity(id=row["id"], slug=row["slug"], created_at=row["created_at"])

    def get_version(self, version_id: UUID) -> AuthoringCaseVersion | None:
        with self._engine.connect() as connection:
            row = self._version_row(connection, version_id)
        return self._version_from_row(row) if row else None

    def list_versions(self, case_id: UUID) -> tuple[AuthoringCaseVersion, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, case_id, version_no, lifecycle_state, aggregate,
                           created_at, published_at
                    FROM editorial.case_version
                    WHERE case_id = :case_id
                    ORDER BY version_no
                    """
                ),
                {"case_id": case_id},
            ).mappings().all()
        return tuple(self._version_from_row(row) for row in rows)

    def next_version_no(self, case_id: UUID) -> int:
        with self._engine.connect() as connection:
            value = connection.execute(
                text(
                    """
                    SELECT COALESCE(MAX(version_no), 0) + 1
                    FROM editorial.case_version
                    WHERE case_id = :case_id
                    """
                ),
                {"case_id": case_id},
            ).scalar_one()
        return int(value)

    def save_draft(
        self,
        version: AuthoringCaseVersion,
        *,
        create_audit: LifecycleAuditEntry | None = None,
    ) -> None:
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT lifecycle_state, case_id, version_no
                        FROM editorial.case_version
                        WHERE id = :version_id
                        FOR UPDATE
                        """
                    ),
                    {"version_id": version.id},
                ).mappings().one_or_none()

                if row is None:
                    self._insert_new_revision(
                        connection,
                        version=version,
                        create_audit=create_audit,
                    )
                    return

                if create_audit is not None:
                    raise ValueError("creation audit is only valid for a new version")
                if row["lifecycle_state"] != ContentLifecycle.DRAFT.value:
                    raise ValueError("only DRAFT versions are editable")
                if row["case_id"] != version.case_id or row["version_no"] != version.version_no:
                    raise ValueError("stable version identity cannot change")
                if version.state is not ContentLifecycle.DRAFT:
                    raise ValueError("save_draft cannot change lifecycle state")

                connection.execute(
                    text(
                        """
                        UPDATE editorial.case_version
                        SET aggregate = CAST(:aggregate AS jsonb), updated_at = now()
                        WHERE id = :version_id
                        """
                    ),
                    {
                        "version_id": version.id,
                        "aggregate": json.dumps(self._document(version)),
                    },
                )
        except IntegrityError as exc:
            raise ValueError("draft version conflicts with existing authoring state") from exc

    def transition(
        self,
        *,
        version: AuthoringCaseVersion,
        expected_state: ContentLifecycle,
        audit: LifecycleAuditEntry,
    ) -> AuthoringCaseVersion:
        with self._engine.begin() as connection:
            row = self._lock_version(connection, version.id)
            if row is None:
                raise ValueError("version does not exist")
            if row["lifecycle_state"] != expected_state.value:
                raise ValueError("content lifecycle changed concurrently")

            connection.execute(
                text(
                    """
                    UPDATE editorial.case_version
                    SET lifecycle_state = :state,
                        aggregate = CAST(:aggregate AS jsonb),
                        updated_at = now(),
                        published_at = :published_at
                    WHERE id = :version_id
                    """
                ),
                {
                    "version_id": version.id,
                    "state": version.state.value,
                    "aggregate": json.dumps(self._document(version)),
                    "published_at": version.published_at,
                },
            )
            if version.state is ContentLifecycle.WITHDRAWN:
                self._withdraw_consumer_version(connection, version)
            self._insert_audit(connection, audit)
        return version

    def publish_atomically(
        self,
        *,
        version: AuthoringCaseVersion,
        expected_state: ContentLifecycle,
        audit: LifecycleAuditEntry,
    ) -> tuple[AuthoringCaseVersion, AuthoringCaseVersion | None]:
        try:
            with self._engine.begin() as connection:
                self._lock_case(connection, version.case_id)
                target_row = self._lock_version(connection, version.id)
                if target_row is None:
                    raise ValueError("version does not exist")
                if target_row["lifecycle_state"] != expected_state.value:
                    raise ValueError("content lifecycle changed concurrently")

                previous_row = connection.execute(
                    text(
                        """
                        SELECT id, case_id, version_no, lifecycle_state, aggregate,
                               created_at, published_at
                        FROM editorial.case_version
                        WHERE case_id = :case_id
                          AND lifecycle_state = 'PUBLISHED'
                          AND id <> :version_id
                        FOR UPDATE
                        """
                    ),
                    {"case_id": version.case_id, "version_id": version.id},
                ).mappings().one_or_none()
                previous = self._version_from_row(previous_row) if previous_row else None

                if previous is not None:
                    connection.execute(
                        text(
                            """
                            UPDATE editorial.case_version
                            SET lifecycle_state = 'SUPERSEDED', updated_at = now()
                            WHERE id = :previous_id
                            """
                        ),
                        {"previous_id": previous.id},
                    )
                    connection.execute(
                        text(
                            """
                            UPDATE content.case_version
                            SET status = 'SUPERSEDED', accepts_weighs = false
                            WHERE id = :previous_id AND status = 'PUBLISHED'
                            """
                        ),
                        {"previous_id": previous.id},
                    )
                    self._insert_audit(
                        connection,
                        LifecycleAuditEntry.create(
                            version=previous,
                            actor_ref=audit.actor_ref,
                            command="supersede_on_publish",
                            previous_state=ContentLifecycle.PUBLISHED,
                            new_state=ContentLifecycle.SUPERSEDED,
                            rationale=f"Superseded by version {version.version_no}",
                            occurred_at=audit.occurred_at,
                        ),
                    )

                self._materialize_consumer(connection, version)
                connection.execute(
                    text(
                        """
                        UPDATE editorial.case_version
                        SET lifecycle_state = 'PUBLISHED',
                            aggregate = CAST(:aggregate AS jsonb),
                            updated_at = now(),
                            published_at = :published_at
                        WHERE id = :version_id
                        """
                    ),
                    {
                        "version_id": version.id,
                        "aggregate": json.dumps(self._document(version)),
                        "published_at": version.published_at,
                    },
                )
                self._insert_audit(connection, audit)
                return version, previous
        except IntegrityError as exc:
            raise ValueError("publication conflicts with existing published content") from exc

    def list_audit(self, case_id: UUID) -> tuple[LifecycleAuditEntry, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT audit_id, case_id, case_version_id, actor_ref, command,
                           previous_state, new_state, rationale, occurred_at
                    FROM editorial.lifecycle_audit
                    WHERE case_id = :case_id
                    ORDER BY occurred_at, audit_id
                    """
                ),
                {"case_id": case_id},
            ).mappings().all()
        return tuple(
            LifecycleAuditEntry(
                audit_id=row["audit_id"],
                case_id=row["case_id"],
                case_version_id=row["case_version_id"],
                actor_ref=row["actor_ref"],
                command=row["command"],
                previous_state=(
                    ContentLifecycle(row["previous_state"])
                    if row["previous_state"] is not None
                    else None
                ),
                new_state=ContentLifecycle(row["new_state"]),
                rationale=row["rationale"],
                occurred_at=row["occurred_at"],
            )
            for row in rows
        )

    def _insert_new_revision(
        self,
        connection: Connection,
        *,
        version: AuthoringCaseVersion,
        create_audit: LifecycleAuditEntry | None,
    ) -> None:
        if create_audit is None:
            raise ValueError("new authoring versions require a creation audit")
        if version.state is not ContentLifecycle.DRAFT:
            raise ValueError("new authoring versions must start as DRAFT")
        self._lock_case(connection, version.case_id)
        expected_version = connection.execute(
            text(
                """
                SELECT COALESCE(MAX(version_no), 0) + 1
                FROM editorial.case_version
                WHERE case_id = :case_id
                """
            ),
            {"case_id": version.case_id},
        ).scalar_one()
        if int(expected_version) != version.version_no:
            raise ValueError("version number changed concurrently")
        self._insert_version(connection, version)
        self._insert_audit(connection, create_audit)

    def _materialize_consumer(
        self,
        connection: Connection,
        version: AuthoringCaseVersion,
    ) -> None:
        identity = connection.execute(
            text("SELECT slug FROM editorial.case_item WHERE id = :case_id"),
            {"case_id": version.case_id},
        ).mappings().one()
        connection.execute(
            text(
                """
                INSERT INTO content.case_item (
                    id, slug, base_format_code, primary_domain_code,
                    lifecycle_state, content_risk, created_at, updated_at
                )
                VALUES (
                    :case_id, :slug, :base_format, :domain,
                    'PUBLISHED', :risk, now(), now()
                )
                ON CONFLICT (id) DO UPDATE SET
                    slug = EXCLUDED.slug,
                    base_format_code = EXCLUDED.base_format_code,
                    primary_domain_code = EXCLUDED.primary_domain_code,
                    lifecycle_state = 'PUBLISHED',
                    content_risk = EXCLUDED.content_risk,
                    updated_at = now()
                """
            ),
            {
                "case_id": version.case_id,
                "slug": identity["slug"],
                "base_format": version.base_format_code,
                "domain": version.primary_domain_code,
                "risk": version.content_risk,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_version (
                    id, case_id, version_no, status, title, summary, accepts_weighs,
                    published_at, created_at, base_format_code,
                    primary_domain_code, content_risk
                )
                VALUES (
                    :id, :case_id, :version_no, 'PUBLISHED', :title, :summary, true,
                    :published_at, :created_at, :base_format, :domain, :risk
                )
                """
            ),
            {
                "id": version.id,
                "case_id": version.case_id,
                "version_no": version.version_no,
                "title": version.title,
                "summary": version.summary,
                "published_at": version.published_at,
                "created_at": version.created_at,
                "base_format": version.base_format_code,
                "domain": version.primary_domain_code,
                "risk": version.content_risk,
            },
        )

        for issue in sorted(version.issues, key=lambda item: (item.sort_order, str(item.id))):
            connection.execute(
                text(
                    """
                    INSERT INTO content.issue (id, case_version_id, code, title, sort_order)
                    VALUES (:id, :case_version_id, :code, :title, :sort_order)
                    """
                ),
                {
                    "id": issue.id,
                    "case_version_id": version.id,
                    "code": issue.code,
                    "title": issue.title,
                    "sort_order": issue.sort_order,
                },
            )
            for question in sorted(
                issue.questions,
                key=lambda item: (item.sort_order, str(item.id)),
            ):
                stable_question_id = uuid4()
                connection.execute(
                    text(
                        """
                        INSERT INTO content.question (id, issue_id, stable_code, sort_order)
                        VALUES (:id, :issue_id, :stable_code, :sort_order)
                        """
                    ),
                    {
                        "id": stable_question_id,
                        "issue_id": issue.id,
                        "stable_code": question.stable_code,
                        "sort_order": question.sort_order,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO content.question_version (
                            id, question_id, version_no, prompt, response_type,
                            response_schema, is_active, is_required, created_at
                        )
                        VALUES (
                            :id, :question_id, 1, :prompt, :response_type,
                            CAST(:response_schema AS jsonb), :is_active, :is_required, now()
                        )
                        """
                    ),
                    {
                        "id": question.id,
                        "question_id": stable_question_id,
                        "prompt": question.prompt,
                        "response_type": question.response_type,
                        "response_schema": json.dumps(question.response_schema),
                        "is_active": question.is_active,
                        "is_required": question.is_required,
                    },
                )

        for source in version.sources:
            connection.execute(
                text(
                    """
                    INSERT INTO content.context_source (
                        id, case_version_id, title, publisher, source_kind,
                        url, published_at, created_at
                    )
                    VALUES (
                        :id, :case_version_id, :title, :publisher, :source_kind,
                        :url, :published_at, now()
                    )
                    """
                ),
                {
                    "id": source.id,
                    "case_version_id": version.id,
                    "title": source.title,
                    "publisher": source.publisher,
                    "source_kind": source.source_kind,
                    "url": source.locator if source.locator.startswith("http") else None,
                    "published_at": source.published_at,
                },
            )

        source_ids = {source.id for source in version.sources}
        for block in sorted(
            version.context_blocks,
            key=lambda item: (item.sort_order, str(item.id)),
        ):
            connection.execute(
                text(
                    """
                    INSERT INTO content.context_block (
                        id, case_version_id, display_order, disclosure_level,
                        title, body, claim_status, created_at
                    )
                    VALUES (
                        :id, :case_version_id, :display_order, :disclosure_level,
                        :title, :body, :claim_status, now()
                    )
                    """
                ),
                {
                    "id": block.id,
                    "case_version_id": version.id,
                    "display_order": block.sort_order,
                    "disclosure_level": block.disclosure_level,
                    "title": block.title,
                    "body": block.body,
                    "claim_status": block.claim_status,
                },
            )
            for source_id in block.source_ids:
                if source_id not in source_ids:
                    raise ValueError("Context block references an unknown source")
                connection.execute(
                    text(
                        """
                        INSERT INTO content.context_block_source (
                            context_block_id, source_id
                        ) VALUES (:context_block_id, :source_id)
                        """
                    ),
                    {"context_block_id": block.id, "source_id": source_id},
                )

    def _withdraw_consumer_version(
        self,
        connection: Connection,
        version: AuthoringCaseVersion,
    ) -> None:
        changed = connection.execute(
            text(
                """
                UPDATE content.case_version
                SET status = 'WITHDRAWN', accepts_weighs = false
                WHERE id = :version_id AND status = 'PUBLISHED'
                RETURNING case_id
                """
            ),
            {"version_id": version.id},
        ).scalar_one_or_none()
        if changed is not None:
            connection.execute(
                text(
                    """
                    UPDATE content.case_item
                    SET lifecycle_state = 'WITHDRAWN', updated_at = now()
                    WHERE id = :case_id
                    """
                ),
                {"case_id": version.case_id},
            )

    def _insert_version(self, connection: Connection, version: AuthoringCaseVersion) -> None:
        connection.execute(
            text(
                """
                INSERT INTO editorial.case_version (
                    id, case_id, version_no, lifecycle_state, aggregate,
                    created_at, updated_at, published_at
                ) VALUES (
                    :id, :case_id, :version_no, :state, CAST(:aggregate AS jsonb),
                    :created_at, now(), :published_at
                )
                """
            ),
            {
                "id": version.id,
                "case_id": version.case_id,
                "version_no": version.version_no,
                "state": version.state.value,
                "aggregate": json.dumps(self._document(version)),
                "created_at": version.created_at,
                "published_at": version.published_at,
            },
        )

    @staticmethod
    def _insert_audit(connection: Connection, audit: LifecycleAuditEntry) -> None:
        connection.execute(
            text(
                """
                INSERT INTO editorial.lifecycle_audit (
                    audit_id, case_id, case_version_id, actor_ref, command,
                    previous_state, new_state, rationale, occurred_at
                ) VALUES (
                    :audit_id, :case_id, :case_version_id, :actor_ref, :command,
                    :previous_state, :new_state, :rationale, :occurred_at
                )
                """
            ),
            {
                "audit_id": audit.audit_id,
                "case_id": audit.case_id,
                "case_version_id": audit.case_version_id,
                "actor_ref": audit.actor_ref,
                "command": audit.command,
                "previous_state": audit.previous_state.value if audit.previous_state else None,
                "new_state": audit.new_state.value,
                "rationale": audit.rationale,
                "occurred_at": audit.occurred_at,
            },
        )

    @staticmethod
    def _lock_case(connection: Connection, case_id: UUID) -> None:
        row = connection.execute(
            text("SELECT id FROM editorial.case_item WHERE id = :case_id FOR UPDATE"),
            {"case_id": case_id},
        ).scalar_one_or_none()
        if row is None:
            raise ValueError("case does not exist")

    @staticmethod
    def _lock_version(connection: Connection, version_id: UUID):
        return connection.execute(
            text(
                """
                SELECT id, case_id, version_no, lifecycle_state, aggregate,
                       created_at, published_at
                FROM editorial.case_version
                WHERE id = :version_id
                FOR UPDATE
                """
            ),
            {"version_id": version_id},
        ).mappings().one_or_none()

    @staticmethod
    def _version_row(connection: Connection, version_id: UUID):
        return connection.execute(
            text(
                """
                SELECT id, case_id, version_no, lifecycle_state, aggregate,
                       created_at, published_at
                FROM editorial.case_version
                WHERE id = :version_id
                """
            ),
            {"version_id": version_id},
        ).mappings().one_or_none()

    @staticmethod
    def _document(version: AuthoringCaseVersion) -> dict[str, Any]:
        return {
            "title": version.title,
            "summary": version.summary,
            "base_format_code": version.base_format_code,
            "primary_domain_code": version.primary_domain_code,
            "content_risk": version.content_risk,
            "modifiers": list(version.modifiers),
            "is_fact_bearing": version.is_fact_bearing,
            "is_real_event": version.is_real_event,
            "required_review_modes": list(version.required_review_modes),
            "completed_review_modes": list(version.completed_review_modes),
            "issues": [
                {
                    "id": str(issue.id),
                    "code": issue.code,
                    "title": issue.title,
                    "sort_order": issue.sort_order,
                    "questions": [
                        {
                            "id": str(question.id),
                            "stable_code": question.stable_code,
                            "prompt": question.prompt,
                            "response_type": question.response_type,
                            "response_schema": question.response_schema,
                            "is_active": question.is_active,
                            "is_required": question.is_required,
                            "sort_order": question.sort_order,
                        }
                        for question in issue.questions
                    ],
                }
                for issue in version.issues
            ],
            "context_blocks": [
                {
                    "id": str(block.id),
                    "title": block.title,
                    "body": block.body,
                    "disclosure_level": block.disclosure_level,
                    "claim_status": block.claim_status,
                    "source_ids": [str(source_id) for source_id in block.source_ids],
                    "sort_order": block.sort_order,
                    "block_type": block.block_type,
                }
                for block in version.context_blocks
            ],
            "sources": [
                {
                    "id": str(source.id),
                    "source_kind": source.source_kind,
                    "locator": source.locator,
                    "title": source.title,
                    "publisher": source.publisher,
                    "published_at": (
                        source.published_at.isoformat() if source.published_at else None
                    ),
                    "claim_status": source.claim_status,
                    "verified": source.verified,
                }
                for source in version.sources
            ],
        }

    @classmethod
    def _version_from_row(cls, row) -> AuthoringCaseVersion:
        document = row["aggregate"]
        issues = tuple(
            AuthoringIssue(
                id=UUID(item["id"]),
                code=item["code"],
                title=item["title"],
                sort_order=item.get("sort_order", 0),
                questions=tuple(
                    AuthoringQuestion(
                        id=UUID(question["id"]),
                        stable_code=question["stable_code"],
                        prompt=question["prompt"],
                        response_type=question["response_type"],
                        response_schema=question.get("response_schema", {}),
                        is_active=question.get("is_active", True),
                        is_required=question.get("is_required", True),
                        sort_order=question.get("sort_order", 0),
                    )
                    for question in item.get("questions", [])
                ),
            )
            for item in document.get("issues", [])
        )
        blocks = tuple(
            AuthoringContextBlock(
                id=UUID(item["id"]),
                title=item["title"],
                body=item["body"],
                disclosure_level=item["disclosure_level"],
                claim_status=item["claim_status"],
                source_ids=tuple(UUID(value) for value in item.get("source_ids", [])),
                sort_order=item.get("sort_order", 0),
                block_type=item.get("block_type", "CONTEXT"),
            )
            for item in document.get("context_blocks", [])
        )
        sources = tuple(
            AuthoringSourceReference(
                id=UUID(item["id"]),
                source_kind=item["source_kind"],
                locator=item["locator"],
                title=item["title"],
                publisher=item["publisher"],
                published_at=(
                    datetime.fromisoformat(item["published_at"])
                    if item.get("published_at")
                    else None
                ),
                claim_status=item.get("claim_status"),
                verified=item.get("verified", False),
            )
            for item in document.get("sources", [])
        )
        return AuthoringCaseVersion(
            id=row["id"],
            case_id=row["case_id"],
            version_no=row["version_no"],
            state=ContentLifecycle(row["lifecycle_state"]),
            title=document["title"],
            summary=document["summary"],
            base_format_code=document["base_format_code"],
            primary_domain_code=document["primary_domain_code"],
            content_risk=document["content_risk"],
            issues=issues,
            context_blocks=blocks,
            sources=sources,
            modifiers=tuple(document.get("modifiers", [])),
            is_fact_bearing=document.get("is_fact_bearing", False),
            is_real_event=document.get("is_real_event", False),
            required_review_modes=tuple(document.get("required_review_modes", [])),
            completed_review_modes=tuple(document.get("completed_review_modes", [])),
            created_at=row["created_at"],
            published_at=row["published_at"],
        )

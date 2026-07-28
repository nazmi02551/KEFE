from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)
from kefe_api.modules.content_authoring.ports import (
    ContentAuthoringRegistry,
    ContentAuthoringRepository,
)


class ContentAuthoringService:
    def __init__(
        self,
        repository: ContentAuthoringRepository,
        registry: ContentAuthoringRegistry,
    ) -> None:
        self._repository = repository
        self._registry = registry

    def create_case(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        actor_ref: str,
    ) -> AuthoringCaseVersion:
        if self._repository.get_case(identity.id) is not None:
            raise DomainError("CONTENT_CASE_ALREADY_EXISTS", "Case already exists", 409)
        if (
            initial_version.case_id != identity.id
            or initial_version.version_no != 1
            or initial_version.state is not ContentLifecycle.DRAFT
        ):
            raise DomainError(
                "CONTENT_INITIAL_VERSION_INVALID",
                "Initial CaseVersion must be version 1 in DRAFT state",
                422,
            )
        audit = LifecycleAuditEntry.create(
            version=initial_version,
            actor_ref=actor_ref,
            command="create_case",
            previous_state=None,
            new_state=ContentLifecycle.DRAFT,
        )
        try:
            self._repository.create_case(
                identity=identity,
                initial_version=initial_version,
                audit=audit,
            )
        except ValueError as exc:
            raise self._conflict(exc) from exc
        return initial_version

    def create_revision(
        self,
        *,
        source_version_id: UUID,
        actor_ref: str,
    ) -> AuthoringCaseVersion:
        source = self._require_version(source_version_id)
        next_version = replace(
            source,
            id=uuid4(),
            version_no=self._repository.next_version_no(source.case_id),
            state=ContentLifecycle.DRAFT,
            created_at=datetime.now(UTC),
            published_at=None,
        )
        try:
            self._repository.save_draft(next_version)
            self._repository.transition(
                version=next_version,
                expected_state=ContentLifecycle.DRAFT,
                audit=LifecycleAuditEntry.create(
                    version=next_version,
                    actor_ref=actor_ref,
                    command="create_revision",
                    previous_state=None,
                    new_state=ContentLifecycle.DRAFT,
                    rationale=f"Created from version {source.version_no}",
                ),
            )
        except ValueError as exc:
            raise self._conflict(exc) from exc
        return next_version

    def save_draft(self, version: AuthoringCaseVersion) -> AuthoringCaseVersion:
        current = self._require_version(version.id)
        if current.state is not ContentLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_PUBLISHED_IMMUTABLE",
                "Only DRAFT CaseVersions can be edited",
                409,
            )
        if version.state is not ContentLifecycle.DRAFT:
            raise DomainError(
                "CONTENT_INVALID_STATE",
                "Draft edits cannot change lifecycle state",
                409,
            )
        try:
            self._repository.save_draft(version)
        except ValueError as exc:
            raise self._conflict(exc) from exc
        return version

    def submit_for_review(self, version_id: UUID, *, actor_ref: str) -> AuthoringCaseVersion:
        return self._transition(
            version_id,
            actor_ref=actor_ref,
            command="submit_for_review",
            allowed_from={ContentLifecycle.DRAFT},
            target=ContentLifecycle.IN_REVIEW,
        )

    def approve(self, version_id: UUID, *, actor_ref: str) -> AuthoringCaseVersion:
        return self._transition(
            version_id,
            actor_ref=actor_ref,
            command="approve",
            allowed_from={ContentLifecycle.IN_REVIEW},
            target=ContentLifecycle.APPROVED,
        )

    def reject(
        self,
        version_id: UUID,
        *,
        actor_ref: str,
        rationale: str,
    ) -> AuthoringCaseVersion:
        if not rationale.strip():
            raise DomainError(
                "CONTENT_REJECTION_RATIONALE_REQUIRED",
                "Rejection rationale is required",
                422,
            )
        return self._transition(
            version_id,
            actor_ref=actor_ref,
            command="reject",
            allowed_from={ContentLifecycle.IN_REVIEW, ContentLifecycle.APPROVED},
            target=ContentLifecycle.DRAFT,
            rationale=rationale.strip(),
        )

    def publish(self, version_id: UUID, *, actor_ref: str) -> AuthoringCaseVersion:
        version = self._require_version(version_id)
        self._assert_state(version, {ContentLifecycle.APPROVED}, "publish")

        failures = self._registry.validate(version)
        if failures:
            raise DomainError(
                "CONTENT_PUBLICATION_INVALID",
                "CaseVersion failed publication validation",
                422,
                meta={
                    "failures": [
                        {"code": item.code, "detail": item.detail, "path": item.path}
                        for item in failures
                    ]
                },
            )

        published_at = datetime.now(UTC)
        published = version.with_state(
            ContentLifecycle.PUBLISHED,
            published_at=published_at,
        )
        audit = LifecycleAuditEntry.create(
            version=version,
            actor_ref=actor_ref,
            command="publish",
            previous_state=ContentLifecycle.APPROVED,
            new_state=ContentLifecycle.PUBLISHED,
            occurred_at=published_at,
        )
        try:
            result, _ = self._repository.publish_atomically(
                version=published,
                expected_state=ContentLifecycle.APPROVED,
                audit=audit,
            )
        except ValueError as exc:
            raise self._conflict(exc) from exc
        return result

    def withdraw(
        self,
        version_id: UUID,
        *,
        actor_ref: str,
        rationale: str,
    ) -> AuthoringCaseVersion:
        if not rationale.strip():
            raise DomainError(
                "CONTENT_WITHDRAW_RATIONALE_REQUIRED",
                "Withdrawal rationale is required",
                422,
            )
        return self._transition(
            version_id,
            actor_ref=actor_ref,
            command="withdraw",
            allowed_from={ContentLifecycle.PUBLISHED},
            target=ContentLifecycle.WITHDRAWN,
            rationale=rationale.strip(),
        )

    def audit_trail(self, case_id: UUID) -> tuple[LifecycleAuditEntry, ...]:
        if self._repository.get_case(case_id) is None:
            raise DomainError("CONTENT_CASE_NOT_FOUND", "Case not found", 404)
        return self._repository.list_audit(case_id)

    def _transition(
        self,
        version_id: UUID,
        *,
        actor_ref: str,
        command: str,
        allowed_from: set[ContentLifecycle],
        target: ContentLifecycle,
        rationale: str | None = None,
    ) -> AuthoringCaseVersion:
        version = self._require_version(version_id)
        self._assert_state(version, allowed_from, command)
        transitioned = version.with_state(target)
        audit = LifecycleAuditEntry.create(
            version=version,
            actor_ref=actor_ref,
            command=command,
            previous_state=version.state,
            new_state=target,
            rationale=rationale,
        )
        try:
            return self._repository.transition(
                version=transitioned,
                expected_state=version.state,
                audit=audit,
            )
        except ValueError as exc:
            raise self._conflict(exc) from exc

    def _require_version(self, version_id: UUID) -> AuthoringCaseVersion:
        version = self._repository.get_version(version_id)
        if version is None:
            raise DomainError("CONTENT_VERSION_NOT_FOUND", "CaseVersion not found", 404)
        return version

    @staticmethod
    def _assert_state(
        version: AuthoringCaseVersion,
        allowed_from: set[ContentLifecycle],
        command: str,
    ) -> None:
        if version.state not in allowed_from:
            raise DomainError(
                "CONTENT_INVALID_STATE",
                f"Cannot {command} CaseVersion from {version.state}",
                409,
                meta={
                    "current_state": version.state.value,
                    "allowed_states": sorted(state.value for state in allowed_from),
                },
            )

    @staticmethod
    def _conflict(exc: ValueError) -> DomainError:
        return DomainError(
            "CONTENT_LIFECYCLE_CONFLICT",
            "Content lifecycle changed concurrently",
            409,
            detail=str(exc),
        )

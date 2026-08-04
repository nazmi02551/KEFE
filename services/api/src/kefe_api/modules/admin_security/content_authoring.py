from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
from kefe_api.modules.content_authoring.service import ContentAuthoringService


class SecuredContentAuthoringService:
    """Admin-only facade that derives audit identity and enforces authorization."""

    def __init__(
        self,
        *,
        authoring: ContentAuthoringService,
        repository: ContentAuthoringRepository,
        security: AdminSecurityService,
    ) -> None:
        self._authoring = authoring
        self._repository = repository
        self._security = security

    def create_case(
        self,
        principal: AdminPrincipal,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_CREATE, now=now)
        return self._authoring.create_case(
            identity=identity,
            initial_version=initial_version,
            actor_ref=principal.audit_actor_ref,
        )

    def create_revision(
        self,
        principal: AdminPrincipal,
        *,
        source_version_id: UUID,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_EDIT, now=now)
        return self._authoring.create_revision(
            source_version_id=source_version_id,
            actor_ref=principal.audit_actor_ref,
        )

    def draft_for_edit(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_EDIT, now=now)
        return self._require_version(version_id)

    def save_draft(
        self,
        principal: AdminPrincipal,
        version: AuthoringCaseVersion,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_EDIT, now=now)
        return self._authoring.save_draft(version)

    def submit_for_review(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_SUBMIT_REVIEW,
            now=now,
        )
        return self._authoring.submit_for_review(
            version_id,
            actor_ref=principal.audit_actor_ref,
        )

    def review_queue(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        offset: int,
        content_risk: str | None = None,
        primary_domain_code: str | None = None,
        now: datetime | None = None,
    ) -> tuple[AuthoringCaseVersion, ...]:
        self._security.authorize(principal, AdminCapability.CONTENT_REVIEW, now=now)
        return self._repository.list_by_state(
            ContentLifecycle.IN_REVIEW,
            limit=limit,
            offset=offset,
            content_risk=content_risk,
            primary_domain_code=primary_domain_code,
        )

    def review_for_inspection(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_REVIEW, now=now)
        version = self._require_version(version_id)
        if version.state is not ContentLifecycle.IN_REVIEW:
            raise DomainError(
                "CONTENT_REVIEW_STATE_REQUIRED",
                "CaseVersion is not awaiting editorial review",
                409,
            )
        return version

    def review_submission(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> LifecycleAuditEntry:
        version = self.review_for_inspection(principal, version_id, now=now)
        submission = self._latest_submission(version)
        if submission is None:
            raise DomainError(
                "CONTENT_REVIEW_SUBMISSION_MISSING",
                "Review submission audit entry is missing",
                409,
            )
        return submission

    def approve(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        version = self.review_for_inspection(principal, version_id, now=now)
        return self._approve_review(
            principal,
            version,
            completed_review_modes=version.completed_review_modes,
            explicit_attestation=False,
            occurred_at=now,
        )

    def approve_with_review_modes(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        completed_review_modes: tuple[str, ...],
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        version = self.review_for_inspection(principal, version_id, now=now)
        return self._approve_review(
            principal,
            version,
            completed_review_modes=completed_review_modes,
            explicit_attestation=True,
            occurred_at=now,
        )

    def reject(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        rationale: str,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        version = self.review_for_inspection(principal, version_id, now=now)
        normalized_rationale = rationale.strip()
        if not normalized_rationale:
            raise DomainError(
                "CONTENT_REJECTION_RATIONALE_REQUIRED",
                "Rejection rationale is required",
                422,
            )
        occurred_at = now or datetime.now(UTC)
        rejected = replace(
            version,
            state=ContentLifecycle.DRAFT,
            completed_review_modes=(),
        )
        audit = LifecycleAuditEntry.create(
            version=version,
            actor_ref=principal.audit_actor_ref,
            command="reject",
            previous_state=ContentLifecycle.IN_REVIEW,
            new_state=ContentLifecycle.DRAFT,
            rationale=normalized_rationale,
            occurred_at=occurred_at,
        )
        return self._transition(rejected, ContentLifecycle.IN_REVIEW, audit)

    def publish(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_PUBLISH, now=now)
        return self._authoring.publish(
            version_id,
            actor_ref=principal.audit_actor_ref,
        )

    def withdraw(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        rationale: str,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_WITHDRAW, now=now)
        return self._authoring.withdraw(
            version_id,
            actor_ref=principal.audit_actor_ref,
            rationale=rationale,
        )

    def audit_trail(
        self,
        principal: AdminPrincipal,
        case_id: UUID,
        *,
        now: datetime | None = None,
    ) -> tuple[LifecycleAuditEntry, ...]:
        self._security.authorize(principal, AdminCapability.AUDIT_READ, now=now)
        return self._authoring.audit_trail(case_id)

    def _approve_review(
        self,
        principal: AdminPrincipal,
        version: AuthoringCaseVersion,
        *,
        completed_review_modes: tuple[str, ...],
        explicit_attestation: bool,
        occurred_at: datetime | None,
    ) -> AuthoringCaseVersion:
        self._security.enforce_reviewer_separation(
            principal=principal,
            submitter_actor_ref=self._latest_submitter(version),
        )
        required = tuple(item.strip() for item in version.required_review_modes)
        if any(not item for item in required) or len(set(required)) != len(required):
            raise DomainError(
                "CONTENT_REQUIRED_REVIEW_MODES_INVALID",
                "CaseVersion required review modes are invalid",
                409,
            )
        if required and not explicit_attestation:
            raise DomainError(
                "CONTENT_REVIEW_ATTESTATION_REQUIRED",
                "Required review modes must be explicitly attested by the reviewer",
                422,
            )

        normalized = tuple(item.strip() for item in completed_review_modes)
        if any(not item for item in normalized) or len(set(normalized)) != len(normalized):
            raise DomainError(
                "CONTENT_REVIEW_MODES_INVALID",
                "Completed review modes must be unique non-empty values",
                422,
            )
        missing = sorted(set(required) - set(normalized))
        unexpected = sorted(set(normalized) - set(required))
        if missing or unexpected:
            raise DomainError(
                "CONTENT_REVIEW_MODES_INCOMPLETE",
                "Completed review modes must exactly match required review modes",
                422,
                meta={"missing": missing, "unexpected": unexpected},
            )

        decision_at = occurred_at or datetime.now(UTC)
        approved = replace(
            version,
            state=ContentLifecycle.APPROVED,
            completed_review_modes=required,
        )
        rationale = (
            "Completed review modes: " + ", ".join(required)
            if required
            else "No required review modes"
        )
        audit = LifecycleAuditEntry.create(
            version=version,
            actor_ref=principal.audit_actor_ref,
            command="approve",
            previous_state=ContentLifecycle.IN_REVIEW,
            new_state=ContentLifecycle.APPROVED,
            rationale=rationale,
            occurred_at=decision_at,
        )
        return self._transition(approved, ContentLifecycle.IN_REVIEW, audit)

    def _transition(
        self,
        version: AuthoringCaseVersion,
        expected_state: ContentLifecycle,
        audit: LifecycleAuditEntry,
    ) -> AuthoringCaseVersion:
        try:
            return self._repository.transition(
                version=version,
                expected_state=expected_state,
                audit=audit,
            )
        except ValueError as exc:
            raise DomainError(
                "CONTENT_LIFECYCLE_CONFLICT",
                "Content lifecycle changed concurrently",
                409,
            ) from exc

    def _require_version(self, version_id: UUID) -> AuthoringCaseVersion:
        version = self._repository.get_version(version_id)
        if version is None:
            raise DomainError("CONTENT_VERSION_NOT_FOUND", "CaseVersion not found", 404)
        return version

    def _latest_submission(
        self,
        version: AuthoringCaseVersion,
    ) -> LifecycleAuditEntry | None:
        submissions = [
            entry
            for entry in self._repository.list_audit(version.case_id)
            if entry.case_version_id == version.id and entry.command == "submit_for_review"
        ]
        if not submissions:
            return None
        return max(submissions, key=lambda entry: entry.occurred_at)

    def _latest_submitter(self, version: AuthoringCaseVersion) -> str | None:
        submission = self._latest_submission(version)
        return submission.actor_ref if submission is not None else None

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
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

    def approve(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_REVIEW, now=now)
        version = self._require_version(version_id)
        self._security.enforce_reviewer_separation(
            principal=principal,
            submitter_actor_ref=self._latest_submitter(version),
        )
        return self._authoring.approve(
            version_id,
            actor_ref=principal.audit_actor_ref,
        )

    def reject(
        self,
        principal: AdminPrincipal,
        version_id: UUID,
        *,
        rationale: str,
        now: datetime | None = None,
    ) -> AuthoringCaseVersion:
        self._security.authorize(principal, AdminCapability.CONTENT_REVIEW, now=now)
        return self._authoring.reject(
            version_id,
            actor_ref=principal.audit_actor_ref,
            rationale=rationale,
        )

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

    def _require_version(self, version_id: UUID) -> AuthoringCaseVersion:
        version = self._repository.get_version(version_id)
        if version is None:
            raise DomainError("CONTENT_VERSION_NOT_FOUND", "CaseVersion not found", 404)
        return version

    def _latest_submitter(self, version: AuthoringCaseVersion) -> str | None:
        submissions = [
            entry
            for entry in self._repository.list_audit(version.case_id)
            if entry.case_version_id == version.id and entry.command == "submit_for_review"
        ]
        if not submissions:
            return None
        return max(submissions, key=lambda entry: entry.occurred_at).actor_ref

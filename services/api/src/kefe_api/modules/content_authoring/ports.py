from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    LifecycleAuditEntry,
    PublicationValidationFailure,
)


class ContentAuthoringRegistry(Protocol):
    def validate(self, version: AuthoringCaseVersion) -> tuple[PublicationValidationFailure, ...]: ...


class ContentAuthoringRepository(Protocol):
    def create_case(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
    ) -> None: ...

    def get_case(self, case_id: UUID) -> CaseIdentity | None: ...

    def get_version(self, version_id: UUID) -> AuthoringCaseVersion | None: ...

    def list_versions(self, case_id: UUID) -> tuple[AuthoringCaseVersion, ...]: ...

    def next_version_no(self, case_id: UUID) -> int: ...

    def save_draft(self, version: AuthoringCaseVersion) -> None: ...

    def transition(
        self,
        *,
        version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
    ) -> AuthoringCaseVersion: ...

    def publish_atomically(
        self,
        *,
        version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
    ) -> tuple[AuthoringCaseVersion, AuthoringCaseVersion | None]: ...

    def list_audit(self, case_id: UUID) -> tuple[LifecycleAuditEntry, ...]: ...

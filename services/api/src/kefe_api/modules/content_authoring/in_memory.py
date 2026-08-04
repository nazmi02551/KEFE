from __future__ import annotations

from dataclasses import replace
from threading import RLock
from uuid import UUID

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)


class InMemoryContentAuthoringRepository:
    def __init__(self) -> None:
        self._cases: dict[UUID, CaseIdentity] = {}
        self._versions: dict[UUID, AuthoringCaseVersion] = {}
        self._version_ids_by_case: dict[UUID, list[UUID]] = {}
        self._audit_by_case: dict[UUID, list[LifecycleAuditEntry]] = {}
        self._lock = RLock()

    def create_case(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
    ) -> None:
        with self._lock:
            if identity.id in self._cases:
                raise ValueError("case already exists")
            if initial_version.case_id != identity.id or initial_version.version_no != 1:
                raise ValueError("invalid initial version")
            self._cases[identity.id] = identity
            self._versions[initial_version.id] = initial_version
            self._version_ids_by_case[identity.id] = [initial_version.id]
            self._audit_by_case[identity.id] = [audit]

    def get_case(self, case_id: UUID) -> CaseIdentity | None:
        with self._lock:
            return self._cases.get(case_id)

    def get_version(self, version_id: UUID) -> AuthoringCaseVersion | None:
        with self._lock:
            return self._versions.get(version_id)

    def list_versions(self, case_id: UUID) -> tuple[AuthoringCaseVersion, ...]:
        with self._lock:
            ids = self._version_ids_by_case.get(case_id, [])
            versions = [self._versions[version_id] for version_id in ids]
            versions.sort(key=lambda version: version.version_no)
            return tuple(versions)

    def list_by_state(
        self,
        state: ContentLifecycle,
        *,
        limit: int,
        offset: int,
        content_risk: str | None = None,
        primary_domain_code: str | None = None,
    ) -> tuple[AuthoringCaseVersion, ...]:
        with self._lock:
            versions = [
                version
                for version in self._versions.values()
                if version.state is state
                and (content_risk is None or version.content_risk == content_risk)
                and (
                    primary_domain_code is None
                    or version.primary_domain_code == primary_domain_code
                )
            ]
            versions.sort(key=lambda version: (version.created_at, str(version.id)), reverse=True)
            return tuple(versions[offset : offset + limit])

    def next_version_no(self, case_id: UUID) -> int:
        with self._lock:
            versions = self.list_versions(case_id)
            return (versions[-1].version_no + 1) if versions else 1

    def save_draft(
        self,
        version: AuthoringCaseVersion,
        *,
        create_audit: LifecycleAuditEntry | None = None,
    ) -> None:
        with self._lock:
            current = self._versions.get(version.id)
            if current is None:
                if version.case_id not in self._cases:
                    raise ValueError("case does not exist")
                if version.state is not ContentLifecycle.DRAFT:
                    raise ValueError("new authoring versions must start as DRAFT")
                if create_audit is None:
                    raise ValueError("new authoring versions require a creation audit")
                if any(
                    item.version_no == version.version_no
                    for item in self.list_versions(version.case_id)
                ):
                    raise ValueError("version number already exists")
                self._versions[version.id] = version
                self._version_ids_by_case.setdefault(version.case_id, []).append(version.id)
                self._audit_by_case.setdefault(version.case_id, []).append(create_audit)
                return
            if create_audit is not None:
                raise ValueError("creation audit is only valid for a new version")
            if current.state is not ContentLifecycle.DRAFT:
                raise ValueError("only DRAFT versions are editable")
            if version.state is not ContentLifecycle.DRAFT:
                raise ValueError("save_draft cannot change lifecycle state")
            if version.case_id != current.case_id or version.version_no != current.version_no:
                raise ValueError("stable version identity cannot change")
            self._versions[version.id] = version

    def transition(
        self,
        *,
        version: AuthoringCaseVersion,
        expected_state: ContentLifecycle,
        audit: LifecycleAuditEntry,
    ) -> AuthoringCaseVersion:
        with self._lock:
            current = self._versions.get(version.id)
            if current is None:
                raise ValueError("version does not exist")
            if current.state is not expected_state:
                raise ValueError("content lifecycle changed concurrently")
            self._versions[version.id] = version
            self._audit_by_case.setdefault(version.case_id, []).append(audit)
            return version

    def publish_atomically(
        self,
        *,
        version: AuthoringCaseVersion,
        expected_state: ContentLifecycle,
        audit: LifecycleAuditEntry,
    ) -> tuple[AuthoringCaseVersion, AuthoringCaseVersion | None]:
        with self._lock:
            current = self._versions.get(version.id)
            if current is None:
                raise ValueError("version does not exist")
            if current.state is not expected_state:
                raise ValueError("content lifecycle changed concurrently")

            previous_published: AuthoringCaseVersion | None = None
            for candidate_id in self._version_ids_by_case.get(version.case_id, []):
                if candidate_id == version.id:
                    continue
                candidate = self._versions[candidate_id]
                if candidate.state is ContentLifecycle.PUBLISHED:
                    previous_published = replace(candidate, state=ContentLifecycle.SUPERSEDED)
                    self._versions[candidate_id] = previous_published
                    self._audit_by_case.setdefault(version.case_id, []).append(
                        LifecycleAuditEntry.create(
                            version=candidate,
                            actor_ref=audit.actor_ref,
                            command="supersede_on_publish",
                            previous_state=ContentLifecycle.PUBLISHED,
                            new_state=ContentLifecycle.SUPERSEDED,
                            rationale=f"Superseded by version {version.version_no}",
                            occurred_at=audit.occurred_at,
                        )
                    )
                    break

            self._versions[version.id] = version
            self._audit_by_case.setdefault(version.case_id, []).append(audit)
            return version, previous_published

    def list_audit(self, case_id: UUID) -> tuple[LifecycleAuditEntry, ...]:
        with self._lock:
            return tuple(self._audit_by_case.get(case_id, ()))

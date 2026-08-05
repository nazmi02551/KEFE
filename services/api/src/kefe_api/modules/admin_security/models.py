from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class AdminRole(StrEnum):
    EDITOR = "EDITOR"
    REVIEWER = "REVIEWER"
    PUBLISHER = "PUBLISHER"
    TAXONOMY_MANAGER = "TAXONOMY_MANAGER"
    ACCESS_ADMIN = "ACCESS_ADMIN"


class AdminCapability(StrEnum):
    CONTENT_CREATE = "CONTENT_CREATE"
    CONTENT_PROJECT = "CONTENT_PROJECT"
    CONTENT_EDIT = "CONTENT_EDIT"
    CONTENT_SUBMIT_REVIEW = "CONTENT_SUBMIT_REVIEW"
    CONTENT_REVIEW = "CONTENT_REVIEW"
    CONTENT_MODERATE = "CONTENT_MODERATE"
    CONTENT_PUBLISH = "CONTENT_PUBLISH"
    CONTENT_WITHDRAW = "CONTENT_WITHDRAW"
    SOURCE_VERIFY = "SOURCE_VERIFY"
    SOURCE_MANAGE = "SOURCE_MANAGE"
    SOURCE_APPROVE = "SOURCE_APPROVE"
    SOURCE_ACTIVATE = "SOURCE_ACTIVATE"
    RISK_REVIEW = "RISK_REVIEW"
    TAXONOMY_MANAGE = "TAXONOMY_MANAGE"
    ADMIN_ACCESS_MANAGE = "ADMIN_ACCESS_MANAGE"
    AUDIT_READ = "AUDIT_READ"


class AdminSubjectState(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class AdminSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class AdminPrincipal:
    admin_subject_id: UUID
    session_id: UUID
    roles: frozenset[AdminRole]
    direct_capabilities: frozenset[AdminCapability]
    authenticated_at: datetime
    mfa_satisfied_at: datetime | None
    step_up_at: datetime | None
    expires_at: datetime
    last_seen_at: datetime

    @property
    def audit_actor_ref(self) -> str:
        return f"admin:{self.admin_subject_id}"


@dataclass(frozen=True, slots=True)
class AdminSessionResolution:
    status: AdminSessionStatus
    principal: AdminPrincipal | None = None


@dataclass(frozen=True, slots=True)
class IssuedAdminSession:
    session_id: UUID
    session_token: str
    csrf_token: str
    expires_at: datetime

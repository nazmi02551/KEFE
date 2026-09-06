from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class InstitutionResponseType(StrEnum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    COMMITMENT = "COMMITMENT"
    POLICY_CHANGE = "POLICY_CHANGE"
    FACTUAL_CLARIFICATION = "FACTUAL_CLARIFICATION"
    DECLINE_WITH_REASON = "DECLINE_WITH_REASON"


class AuthorityVerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class InstitutionResponse:
    response_id: UUID
    case_version_id: UUID
    institution_name: str
    authority_role: str
    verification_status: AuthorityVerificationStatus
    response_type: InstitutionResponseType
    statement: str
    published_at: datetime
    milestone_date: datetime | None = None

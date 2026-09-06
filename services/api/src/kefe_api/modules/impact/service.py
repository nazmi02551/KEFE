from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)


class InstitutionResponseService:
    def __init__(self) -> None:
        self._responses_by_case: dict[UUID, list[InstitutionResponse]] = {}

    def publish_response(
        self,
        *,
        case_version_id: UUID,
        institution_name: str,
        authority_role: str,
        response_type: InstitutionResponseType,
        statement: str,
        verification_status: AuthorityVerificationStatus = AuthorityVerificationStatus.VERIFIED,
        milestone_date: datetime | None = None,
    ) -> InstitutionResponse:
        cleaned_institution = institution_name.strip()
        cleaned_role = authority_role.strip()
        cleaned_statement = statement.strip()

        if len(cleaned_institution) < 2:
            raise ValueError("institution_name must have at least 2 characters")
        if len(cleaned_role) < 2:
            raise ValueError("authority_role must have at least 2 characters")
        if len(cleaned_statement) < 10:
            raise ValueError("statement must have at least 10 characters")

        response = InstitutionResponse(
            response_id=uuid4(),
            case_version_id=case_version_id,
            institution_name=cleaned_institution,
            authority_role=cleaned_role,
            verification_status=verification_status,
            response_type=response_type,
            statement=cleaned_statement,
            published_at=datetime.now(UTC),
            milestone_date=milestone_date,
        )

        self._responses_by_case.setdefault(case_version_id, []).append(response)
        return response

    def list_verified_responses(self, case_version_id: UUID) -> list[InstitutionResponse]:
        responses = self._responses_by_case.get(case_version_id, [])
        return [
            r for r in responses
            if r.verification_status == AuthorityVerificationStatus.VERIFIED
        ]

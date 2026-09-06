from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib


class InstitutionType(StrEnum):
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    MUNICIPAL_LOCAL = "MUNICIPAL_LOCAL"
    CORPORATE_ENTERPRISE = "CORPORATE_ENTERPRISE"
    CIVIL_SOCIETY = "CIVIL_SOCIETY"


@dataclass(frozen=True, slots=True)
class VerifiedInstitutionResponseResult:
    response_id: str
    signal_id: str
    institution_name: str
    institution_type: InstitutionType
    response_body: str
    verification_fingerprint: str
    responded_at_utc: str


class VerifiedInstitutionResponseService:
    @staticmethod
    def register_response(
        *,
        response_id: str,
        signal_id: str,
        institution_name: str,
        institution_type: InstitutionType,
        response_body: str,
        signing_key_id: str,
        timestamp: datetime | None = None,
    ) -> VerifiedInstitutionResponseResult:
        if len(institution_name.strip()) < 3:
            raise ValueError("institution_name must have at least 3 characters")
        if len(response_body.strip()) < 10:
            raise ValueError("response_body must have at least 10 characters")
        if len(signing_key_id.strip()) < 3:
            raise ValueError("signing_key_id must have at least 3 characters")

        ts = timestamp or datetime.now(timezone.utc)
        ts_str = ts.isoformat()

        raw_payload = f"{response_id}:{signal_id}:{institution_name}:{signing_key_id}:{ts_str}"
        fingerprint = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        return VerifiedInstitutionResponseResult(
            response_id=response_id.strip(),
            signal_id=signal_id.strip(),
            institution_name=institution_name.strip(),
            institution_type=institution_type,
            response_body=response_body.strip(),
            verification_fingerprint=fingerprint,
            responded_at_utc=ts_str,
        )

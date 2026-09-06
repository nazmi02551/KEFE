from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DecisionReceiptResult:
    receipt_id: str
    case_version_id: UUID
    committed_choice: str
    integrity_digest: str
    timestamp_utc: str


class DecisionReceiptGenerator:
    @staticmethod
    def generate(
        *,
        case_version_id: UUID,
        committed_choice: str,
        user_pseudonym: str,
        timestamp: datetime | None = None,
    ) -> DecisionReceiptResult:
        if len(committed_choice.strip()) < 1:
            raise ValueError("committed_choice must not be empty")
        if len(user_pseudonym.strip()) < 3:
            raise ValueError("user_pseudonym must have at least 3 characters")

        ts = timestamp or datetime.now(timezone.utc)
        ts_str = ts.isoformat()

        raw_payload = f"{case_version_id}:{user_pseudonym}:{committed_choice}:{ts_str}"
        digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        receipt_id = f"kefe-rcpt-{digest[:16]}"

        return DecisionReceiptResult(
            receipt_id=receipt_id,
            case_version_id=case_version_id,
            committed_choice=committed_choice.strip(),
            integrity_digest=digest,
            timestamp_utc=ts_str,
        )

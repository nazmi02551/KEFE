from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.ports import (
    ProposalReviewQueueRepository,
)
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueQuery,
    ProposalQueueRecord,
    ProposalQueueReviewState,
)


@dataclass(frozen=True, slots=True)
class ProposalQueuePage:
    items: tuple[ProposalQueueRecord, ...]
    next_cursor: str | None


class SecuredProposalQueueService:
    def __init__(
        self,
        *,
        repository: ProposalReviewQueueRepository,
        security: AdminSecurityService,
    ) -> None:
        self._repository = repository
        self._security = security

    def list_queue(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        cursor: str | None = None,
        review_state: ProposalQueueReviewState | None = None,
        proposal_kind: str | None = None,
        risk_code: str | None = None,
        run_id: UUID | None = None,
        pipeline_code: str | None = None,
        now: datetime | None = None,
    ) -> ProposalQueuePage:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_REVIEW,
            now=now,
        )
        after_created_at, after_proposal_id = self._decode_cursor(cursor)
        rows = self._repository.list_proposal_queue(
            ProposalQueueQuery(
                limit=limit + 1,
                review_state=review_state,
                proposal_kind=proposal_kind,
                risk_code=risk_code,
                run_id=run_id,
                pipeline_code=pipeline_code,
                after_created_at=after_created_at,
                after_proposal_id=after_proposal_id,
            )
        )
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit and items:
            next_cursor = self._encode_cursor(items[-1])
        return ProposalQueuePage(items=items, next_cursor=next_cursor)

    def detail(
        self,
        principal: AdminPrincipal,
        proposal_id: UUID,
        *,
        now: datetime | None = None,
    ) -> ProposalQueueRecord:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_REVIEW,
            now=now,
        )
        record = self._repository.get_proposal_queue_record(proposal_id)
        if record is None:
            raise DomainError(
                "INGESTION_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
            )
        return record

    @staticmethod
    def _encode_cursor(record: ProposalQueueRecord) -> str:
        payload = json.dumps(
            {
                "created_at": record.proposal.created_at.isoformat(),
                "proposal_id": str(record.proposal.id),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str | None) -> tuple[datetime | None, UUID | None]:
        if cursor is None:
            return None, None
        try:
            padding = "=" * (-len(cursor) % 4)
            decoded = base64.b64decode(
                cursor + padding,
                altchars=b"-_",
                validate=True,
            )
            payload = json.loads(decoded.decode())
            if not isinstance(payload, dict) or set(payload) != {
                "created_at",
                "proposal_id",
            }:
                raise ValueError("cursor shape is invalid")
            created_at = datetime.fromisoformat(payload["created_at"])
            if created_at.tzinfo is None:
                raise ValueError("cursor datetime requires timezone")
            proposal_id = UUID(payload["proposal_id"])
            return created_at, proposal_id
        except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DomainError(
                "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID",
                "Proposal queue cursor is invalid",
                422,
            ) from exc

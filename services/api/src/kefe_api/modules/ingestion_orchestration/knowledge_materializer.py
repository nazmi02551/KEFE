from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
)
from kefe_api.modules.ingestion_orchestration.ports import IngestionOrchestrationRepository
from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentTargetKind,
    Claim,
    ClaimAssertion,
    ClaimAssessment,
    ClaimRelation,
    ClaimState,
    ClaimType,
    EvidenceLink,
    EvidenceRelation,
    EvidenceTargetKind,
    ReviewState,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository


class KnowledgeProposalMaterializer:
    def __init__(
        self,
        *,
        knowledge_repository: KnowledgeRepository,
        orchestration_repository: IngestionOrchestrationRepository,
    ) -> None:
        self._knowledge = knowledge_repository
        self._orchestration = orchestration_repository

    def materialize(
        self,
        *,
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> tuple[str, UUID]:
        kind = proposal.proposal_kind
        target_id = self._target_id(proposal.id, kind)
        handlers = {
            "CLAIM": self._claim,
            "CLAIM_ASSESSMENT": self._claim_assessment,
            "CLAIM_ASSERTION": self._claim_assertion,
            "EVIDENCE_LINK": self._evidence_link,
            "CLAIM_RELATION": self._claim_relation,
            "ARGUMENT": self._argument,
            "ARGUMENT_RELATION": self._argument_relation,
        }
        handler = handlers.get(kind)
        if handler is None:
            raise ValueError(f"proposal kind is not materializable into knowledge: {kind}")
        handler(proposal, review, target_id)
        return kind, target_id

    def _claim(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        del review
        payload = proposal.payload
        item = Claim(
            id=target_id,
            normalized_text=self._required_text(payload, "normalized_text"),
            language_code=self._required_text(payload, "language_code"),
            created_at=self._datetime(payload.get("created_at"), proposal.created_at),
        )
        self._safe_add(lambda: self._knowledge.add_claim(item))

    def _claim_assessment(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        claim_id = self._resolve_ref(
            payload,
            direct_key="claim_id",
            proposal_key="claim_proposal_id",
            target_kind="CLAIM",
        )
        taxonomy_version = (
            self._optional_text(payload, "taxonomy_version")
            or proposal.taxonomy_version
        )
        if not taxonomy_version:
            raise ValueError("CLAIM_ASSESSMENT requires taxonomy_version")
        item = ClaimAssessment(
            id=target_id,
            claim_id=claim_id,
            claim_type=ClaimType(self._required_text(payload, "claim_type")),
            claim_state=ClaimState(self._required_text(payload, "claim_state")),
            taxonomy_version=taxonomy_version,
            review_state=ReviewState.ACCEPTED,
            assessed_at=self._datetime(payload.get("assessed_at"), review.decided_at),
            methodology_version=(
                self._optional_text(payload, "methodology_version")
                or proposal.methodology_version
            ),
            reviewer_ref=review.reviewer_ref,
            rationale_code=self._optional_text(payload, "rationale_code"),
            provenance_ref=self._provenance(proposal, review),
        )
        self._safe_add(lambda: self._knowledge.add_claim_assessment(item))

    def _claim_assertion(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        item = ClaimAssertion(
            id=target_id,
            claim_id=self._resolve_ref(
                payload,
                direct_key="claim_id",
                proposal_key="claim_proposal_id",
                target_kind="CLAIM",
            ),
            claimant_kind=self._required_text(payload, "claimant_kind"),
            claimant_ref=self._required_text(payload, "claimant_ref"),
            asserted_at=self._datetime(payload.get("asserted_at"), proposal.created_at),
            source_artifact_id=self._optional_uuid(payload.get("source_artifact_id")),
            normalized_artifact_id=self._optional_uuid(
                payload.get("normalized_artifact_id")
            ),
            provenance_ref=self._provenance(proposal, review),
        )
        self._safe_add(lambda: self._knowledge.add_claim_assertion(item))

    def _evidence_link(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        item = EvidenceLink(
            id=target_id,
            claim_id=self._resolve_ref(
                payload,
                direct_key="claim_id",
                proposal_key="claim_proposal_id",
                target_kind="CLAIM",
            ),
            target_kind=EvidenceTargetKind(
                self._required_text(payload, "evidence_target_kind")
            ),
            target_id=self._uuid(payload.get("evidence_target_id"), "evidence_target_id"),
            relation=EvidenceRelation(self._required_text(payload, "relation")),
            review_state=ReviewState.ACCEPTED,
            provenance_ref=self._provenance(proposal, review),
            created_at=self._datetime(payload.get("created_at"), review.decided_at),
        )
        self._safe_add(lambda: self._knowledge.add_evidence_link(item))

    def _claim_relation(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        taxonomy_version = (
            self._optional_text(payload, "taxonomy_version")
            or proposal.taxonomy_version
        )
        if not taxonomy_version:
            raise ValueError("CLAIM_RELATION requires taxonomy_version")
        item = ClaimRelation(
            id=target_id,
            from_claim_id=self._resolve_ref(
                payload,
                direct_key="from_claim_id",
                proposal_key="from_claim_proposal_id",
                target_kind="CLAIM",
            ),
            to_claim_id=self._resolve_ref(
                payload,
                direct_key="to_claim_id",
                proposal_key="to_claim_proposal_id",
                target_kind="CLAIM",
            ),
            relation_code=self._required_text(payload, "relation_code"),
            taxonomy_version=taxonomy_version,
            review_state=ReviewState.ACCEPTED,
            provenance_ref=self._provenance(proposal, review),
            created_at=self._datetime(payload.get("created_at"), review.decided_at),
        )
        self._safe_add(lambda: self._knowledge.add_claim_relation(item))

    def _argument(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        item = Argument(
            id=target_id,
            body=self._required_text(payload, "body"),
            language_code=self._required_text(payload, "language_code"),
            review_state=ReviewState.ACCEPTED,
            created_at=self._datetime(payload.get("created_at"), review.decided_at),
            normalized_artifact_id=self._optional_uuid(
                payload.get("normalized_artifact_id")
            ),
            source_artifact_id=self._optional_uuid(payload.get("source_artifact_id")),
            author_or_claimant_ref=self._optional_text(
                payload,
                "author_or_claimant_ref",
            ),
            provenance_ref=self._provenance(proposal, review),
        )
        self._safe_add(lambda: self._knowledge.add_argument(item))

    def _argument_relation(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        payload = proposal.payload
        target_kind = ArgumentTargetKind(
            self._required_text(payload, "target_kind")
        )
        taxonomy_version = (
            self._optional_text(payload, "taxonomy_version")
            or proposal.taxonomy_version
        )
        if not taxonomy_version:
            raise ValueError("ARGUMENT_RELATION requires taxonomy_version")
        argument_id = self._resolve_ref(
            payload,
            direct_key="argument_id",
            proposal_key="argument_proposal_id",
            target_kind="ARGUMENT",
        )
        if target_kind is ArgumentTargetKind.CLAIM:
            target_ref = self._resolve_ref(
                payload,
                direct_key="target_ref",
                proposal_key="target_proposal_id",
                target_kind="CLAIM",
            )
        elif target_kind is ArgumentTargetKind.ARGUMENT:
            target_ref = self._resolve_ref(
                payload,
                direct_key="target_ref",
                proposal_key="target_proposal_id",
                target_kind="ARGUMENT",
            )
        else:
            target_ref = self._uuid(payload.get("target_ref"), "target_ref")
        item = ArgumentRelation(
            id=target_id,
            argument_id=argument_id,
            target_kind=target_kind,
            target_ref=target_ref,
            relation=ArgumentRelationKind(self._required_text(payload, "relation")),
            taxonomy_version=taxonomy_version,
            review_state=ReviewState.ACCEPTED,
            created_at=self._datetime(payload.get("created_at"), review.decided_at),
            provenance_ref=self._provenance(proposal, review),
        )
        self._safe_add(lambda: self._knowledge.add_argument_relation(item))

    def _resolve_ref(
        self,
        payload: dict[str, Any],
        *,
        direct_key: str,
        proposal_key: str,
        target_kind: str,
    ) -> UUID:
        if payload.get(direct_key) is not None:
            return self._uuid(payload[direct_key], direct_key)
        proposal_value = payload.get(proposal_key)
        if proposal_value is None:
            raise ValueError(f"{direct_key} or {proposal_key} is required")
        proposal_id = self._uuid(proposal_value, proposal_key)
        materialization = self._orchestration.find_materialization(
            proposal_id,
            target_kind=target_kind,
        )
        if materialization is None:
            raise ValueError(f"referenced proposal is not materialized as {target_kind}")
        return materialization.target_id

    @staticmethod
    def _target_id(proposal_id: UUID, target_kind: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"kefe:proposal:{proposal_id}:{target_kind}")

    @staticmethod
    def _uuid(value: Any, field_name: str) -> UUID:
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as exc:
                raise ValueError(f"{field_name} must be a UUID") from exc
        raise ValueError(f"{field_name} must be a UUID")

    @classmethod
    def _optional_uuid(cls, value: Any) -> UUID | None:
        if value is None:
            return None
        return cls._uuid(value, "uuid")

    @staticmethod
    def _required_text(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-blank string")
        return value

    @staticmethod
    def _optional_text(payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-blank string when provided")
        return value

    @staticmethod
    def _datetime(value: Any, fallback: datetime) -> datetime:
        if value is None:
            return fallback
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        raise ValueError("datetime value must be ISO-8601 text or datetime")

    @staticmethod
    def _provenance(
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> str:
        base = proposal.provenance_ref or f"proposal:{proposal.id}"
        return f"{base};review:{review.id}"

    @staticmethod
    def _safe_add(action) -> None:
        try:
            action()
        except ValueError as exc:
            if "already exists" not in str(exc) and "persistence invariant" not in str(exc):
                raise

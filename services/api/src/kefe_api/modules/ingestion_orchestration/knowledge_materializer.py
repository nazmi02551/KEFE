from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.ports import IngestionOrchestrationRepository
from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentTargetKind,
    ArtifactKind,
    Claim,
    ClaimAssertion,
    ClaimAssessment,
    ClaimRelation,
    ClaimState,
    ClaimType,
    EvidenceLink,
    EvidenceRelation,
    EvidenceTargetKind,
    NormalizedArtifact,
    ReviewState,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.source_evidence import canonical_storage_ref

_FEED_ITEM_KIND = "FEED_ITEM"
_FEED_ITEM_SCHEMA_REF = "kefe.feed-item"
_FEED_ITEM_SCHEMA_VERSION = "1.0.0"
_FEED_ITEM_RISK_CODE = "UNREVIEWED_EXTERNAL_FEED_ITEM"
_NORMALIZED_ARTIFACT_KIND = "NORMALIZED_ARTIFACT"
_NORMALIZED_FEED_SCHEMA_REF = "kefe.normalized-feed-item"
_NORMALIZED_FEED_SCHEMA_VERSION = "1.0.0"
_FEED_FORMATS = frozenset({"ATOM_1_0", "RSS_2_0"})
_FEED_ITEM_PAYLOAD_KEYS = frozenset(
    {
        "source_artifact_id",
        "feed_content_hash",
        "feed_storage_ref",
        "feed_format",
        "feed_title",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "summary_text",
    }
)
_MAX_ITEM_ID_CHARS = 4096
_MAX_TITLE_CHARS = 4096
_MAX_URL_CHARS = 4096
_MAX_SUMMARY_CHARS = 16_384
_MAX_REVIEWER_REF_CHARS = 512
_MAX_REVIEW_FIELD_CHARS = 4096
_MAX_METADATA_BYTES = 65_536


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
        if kind == _FEED_ITEM_KIND:
            target_id = self._target_id(proposal.id, _NORMALIZED_ARTIFACT_KIND)
            self._feed_item(proposal, review, target_id)
            return _NORMALIZED_ARTIFACT_KIND, target_id

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
            raise ValueError(
                f"proposal kind is not materializable into knowledge: {kind}"
            )
        handler(proposal, review, target_id)
        return kind, target_id

    def _feed_item(
        self,
        proposal: Proposal,
        review: ProposalReviewDecision,
        target_id: UUID,
    ) -> None:
        if review.proposal_id != proposal.id:
            raise ValueError("feed item review does not reference proposal")
        if review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise ValueError("feed item materialization requires ACCEPTED review")
        self._require_utc(review.decided_at, "review.decided_at")
        reviewer_ref = self._canonical_text(
            review.reviewer_ref,
            "reviewer_ref",
            max_chars=_MAX_REVIEWER_REF_CHARS,
        )
        if proposal.payload_schema_ref != _FEED_ITEM_SCHEMA_REF:
            raise ValueError("FEED_ITEM payload schema is invalid")
        if proposal.payload_schema_version != _FEED_ITEM_SCHEMA_VERSION:
            raise ValueError("FEED_ITEM payload schema version is invalid")
        if proposal.risk_code != _FEED_ITEM_RISK_CODE:
            raise ValueError("FEED_ITEM risk code is invalid")
        if proposal.ai_execution_ref is not None:
            raise ValueError("FEED_ITEM cannot carry an AI execution reference")

        payload = proposal.payload
        if type(payload) is not dict or frozenset(payload) != _FEED_ITEM_PAYLOAD_KEYS:
            raise ValueError("FEED_ITEM payload keys are invalid")

        source_id = self._canonical_uuid_text(
            payload.get("source_artifact_id"),
            "source_artifact_id",
        )
        source = self._knowledge.get_source_artifact(source_id)
        if source is None:
            raise ValueError("FEED_ITEM source artifact does not exist")

        feed_content_hash = self._canonical_text(
            payload.get("feed_content_hash"),
            "feed_content_hash",
            max_chars=71,
        )
        feed_storage_ref = self._canonical_text(
            payload.get("feed_storage_ref"),
            "feed_storage_ref",
            max_chars=96,
        )
        try:
            expected_storage_ref = canonical_storage_ref(feed_content_hash)
        except ValueError as exc:
            raise ValueError("FEED_ITEM content hash is invalid") from exc
        if expected_storage_ref != feed_storage_ref:
            raise ValueError("FEED_ITEM evidence reference does not match content hash")
        if source.content_hash != feed_content_hash:
            raise ValueError("FEED_ITEM content hash does not match SourceArtifact")
        if source.raw_storage_ref != feed_storage_ref:
            raise ValueError("FEED_ITEM evidence reference does not match SourceArtifact")
        if proposal.provenance_ref != feed_storage_ref:
            raise ValueError("FEED_ITEM provenance does not match immutable evidence")

        feed_format = self._canonical_text(
            payload.get("feed_format"),
            "feed_format",
            max_chars=32,
        )
        if feed_format not in _FEED_FORMATS:
            raise ValueError("FEED_ITEM feed format is invalid")
        feed_title = self._canonical_text(
            payload.get("feed_title"),
            "feed_title",
            max_chars=_MAX_TITLE_CHARS,
        )
        item_id = self._canonical_text(
            payload.get("item_id"),
            "item_id",
            max_chars=_MAX_ITEM_ID_CHARS,
        )
        item_title = self._canonical_text(
            payload.get("item_title"),
            "item_title",
            max_chars=_MAX_TITLE_CHARS,
        )
        item_url = self._optional_http_url(payload.get("item_url"))
        published_at = self._optional_utc_datetime_text(
            payload.get("published_at"),
            "published_at",
        )
        summary_text = self._optional_canonical_text(
            payload.get("summary_text"),
            "summary_text",
            max_chars=_MAX_SUMMARY_CHARS,
        )

        normalized_text = (
            item_title
            if summary_text is None
            else f"{item_title}\n\n{summary_text}"
        )
        canonical_content = {
            "schema_ref": _NORMALIZED_FEED_SCHEMA_REF,
            "schema_version": _NORMALIZED_FEED_SCHEMA_VERSION,
            "source_artifact_id": str(source.id),
            "feed_content_hash": feed_content_hash,
            "feed_format": feed_format,
            "feed_title": feed_title,
            "item_id": item_id,
            "item_title": item_title,
            "item_url": item_url,
            "published_at": published_at,
            "summary_text": summary_text,
        }
        content_hash = f"sha256:{stable_payload_hash(canonical_content)}"
        metadata = {
            **canonical_content,
            "feed_storage_ref": feed_storage_ref,
            "proposal_id": str(proposal.id),
            "proposal_payload_hash": proposal.payload_hash,
            "review_id": str(review.id),
            "reviewer_ref": reviewer_ref,
            "reviewed_at": review.decided_at.isoformat(),
            "review_rationale": self._optional_review_text(
                review.rationale,
                "review.rationale",
            ),
            "review_reason_code": self._optional_review_text(
                review.reason_code,
                "review.reason_code",
            ),
            "review_policy_version": self._optional_review_text(
                review.policy_version,
                "review.policy_version",
            ),
            "review_risk_policy_version": self._optional_review_text(
                review.risk_policy_version,
                "review.risk_policy_version",
            ),
            "provenance_ref": self._provenance(proposal, review),
        }
        encoded_metadata = json.dumps(
            metadata,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded_metadata) > _MAX_METADATA_BYTES:
            raise ValueError("FEED_ITEM provenance metadata exceeds byte budget")

        item = NormalizedArtifact(
            id=target_id,
            source_artifact_id=source.id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=review.decided_at,
            content_hash=content_hash,
            text=normalized_text,
            language_code=source.language_code,
            jurisdiction_code=source.jurisdiction_code,
            media_metadata=metadata,
        )
        self._safe_add_exact_normalized(item)

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
        self._safe_add(
            lambda: self._knowledge.add_claim(item),
            lambda: self._knowledge.get_claim(target_id) is not None,
        )

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
        self._safe_add(
            lambda: self._knowledge.add_claim_assessment(item),
            lambda: any(
                current.id == target_id
                for current in self._knowledge.list_claim_assessments(claim_id)
            ),
        )

    def _claim_assertion(
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
        item = ClaimAssertion(
            id=target_id,
            claim_id=claim_id,
            claimant_kind=self._required_text(payload, "claimant_kind"),
            claimant_ref=self._required_text(payload, "claimant_ref"),
            asserted_at=self._datetime(payload.get("asserted_at"), proposal.created_at),
            source_artifact_id=self._optional_uuid(payload.get("source_artifact_id")),
            normalized_artifact_id=self._optional_uuid(
                payload.get("normalized_artifact_id")
            ),
            provenance_ref=self._provenance(proposal, review),
        )
        self._safe_add(
            lambda: self._knowledge.add_claim_assertion(item),
            lambda: any(
                current.id == target_id
                for current in self._knowledge.list_claim_assertions(claim_id)
            ),
        )

    def _evidence_link(
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
        item = EvidenceLink(
            id=target_id,
            claim_id=claim_id,
            target_kind=EvidenceTargetKind(
                self._required_text(payload, "evidence_target_kind")
            ),
            target_id=self._uuid(
                payload.get("evidence_target_id"),
                "evidence_target_id",
            ),
            relation=EvidenceRelation(self._required_text(payload, "relation")),
            review_state=ReviewState.ACCEPTED,
            provenance_ref=self._provenance(proposal, review),
            created_at=self._datetime(payload.get("created_at"), review.decided_at),
        )
        self._safe_add(
            lambda: self._knowledge.add_evidence_link(item),
            lambda: any(
                current.id == target_id
                for current in self._knowledge.list_evidence_links(claim_id)
            ),
        )

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
        from_claim_id = self._resolve_ref(
            payload,
            direct_key="from_claim_id",
            proposal_key="from_claim_proposal_id",
            target_kind="CLAIM",
        )
        item = ClaimRelation(
            id=target_id,
            from_claim_id=from_claim_id,
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
        self._safe_add(
            lambda: self._knowledge.add_claim_relation(item),
            lambda: any(
                current.id == target_id
                for current in self._knowledge.list_claim_relations(from_claim_id)
            ),
        )

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
        self._safe_add(
            lambda: self._knowledge.add_argument(item),
            lambda: self._knowledge.get_argument(target_id) is not None,
        )

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
        self._safe_add(
            lambda: self._knowledge.add_argument_relation(item),
            lambda: any(
                current.id == target_id
                for current in self._knowledge.list_argument_relations(argument_id)
            ),
        )

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
            raise ValueError(
                f"referenced proposal is not materialized as {target_kind}"
            )
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
    def _canonical_uuid_text(cls, value: Any, field_name: str) -> UUID:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be canonical UUID text")
        resolved = cls._uuid(value, field_name)
        if str(resolved) != value:
            raise ValueError(f"{field_name} must be canonical UUID text")
        return resolved

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
    def _canonical_text(value: Any, field_name: str, *, max_chars: int) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be non-blank text")
        if len(value) > max_chars:
            raise ValueError(f"{field_name} exceeds character budget")
        if " ".join(value.split()) != value:
            raise ValueError(f"{field_name} must be canonical whitespace-normalized text")
        return value

    @classmethod
    def _optional_canonical_text(
        cls,
        value: Any,
        field_name: str,
        *,
        max_chars: int,
    ) -> str | None:
        if value is None:
            return None
        return cls._canonical_text(value, field_name, max_chars=max_chars)

    @classmethod
    def _optional_review_text(cls, value: Any, field_name: str) -> str | None:
        if value is None:
            return None
        return cls._canonical_text(
            value,
            field_name,
            max_chars=_MAX_REVIEW_FIELD_CHARS,
        )

    @classmethod
    def _optional_http_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        resolved = cls._canonical_text(
            value,
            "item_url",
            max_chars=_MAX_URL_CHARS,
        )
        try:
            parsed = urlsplit(resolved)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("item_url is invalid") from exc
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("item_url must use http or https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("item_url userinfo is forbidden")
        if parsed.hostname is None or parsed.fragment:
            raise ValueError("item_url host is required and fragment is forbidden")
        if port not in (None, 80, 443):
            raise ValueError("item_url nonstandard port is forbidden")
        return resolved

    @classmethod
    def _optional_utc_datetime_text(
        cls,
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None
        resolved = cls._canonical_text(value, field_name, max_chars=64)
        try:
            parsed = datetime.fromisoformat(resolved)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be ISO-8601 text") from exc
        cls._require_utc(parsed, field_name)
        if parsed.isoformat() != resolved:
            raise ValueError(f"{field_name} must be canonical UTC ISO-8601 text")
        return resolved

    @staticmethod
    def _require_utc(value: datetime, field_name: str) -> None:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be timezone-aware UTC")

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

    def _safe_add_exact_normalized(self, item: NormalizedArtifact) -> None:
        existing = self._knowledge.get_normalized_artifact(item.id)
        if existing is not None:
            if existing != item:
                raise ValueError("conflicting normalized artifact already exists")
            return
        try:
            self._knowledge.add_normalized_artifact(item)
        except ValueError:
            existing = self._knowledge.get_normalized_artifact(item.id)
            if existing == item:
                return
            raise

    @staticmethod
    def _safe_add(
        action: Callable[[], None],
        exists: Callable[[], bool],
    ) -> None:
        if exists():
            return
        try:
            action()
        except ValueError:
            if exists():
                return
            raise

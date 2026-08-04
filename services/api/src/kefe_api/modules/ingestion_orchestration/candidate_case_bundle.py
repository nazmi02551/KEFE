from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    InputArtifactKind,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import FinalStageError
from kefe_api.modules.ingestion_orchestration.source_brief_ingestion import (
    SOURCE_BRIEF_KIND,
    SOURCE_BRIEF_RISK_CODE,
    SOURCE_BRIEF_SCHEMA_REF,
    SOURCE_BRIEF_SCHEMA_VERSION,
    require_source_brief_normalized_artifact,
)
from kefe_api.modules.knowledge.models import ArtifactKind, NormalizedArtifact
from kefe_api.modules.knowledge.ports import KnowledgeRepository

SEED_SCHEMA_REF = "kefe.accepted-source-brief-candidate-seed"
SEED_SCHEMA_VERSION = "1.0.0"
PIPELINE_CODE = "SOURCE_BRIEF_CANDIDATE_BUNDLE"
PIPELINE_VERSION = "1.0.0"
STAGE_CODE = "BUILD_CANDIDATE_BUNDLE"
STAGE_VERSION = "1.0.0"

DECISION_PROBLEM_KIND = "DECISION_PROBLEM"
DECISION_PROBLEM_SCHEMA_REF = "kefe.decision_problem"
QUESTION_DRAFT_KIND = "QUESTION_DRAFT"
QUESTION_DRAFT_SCHEMA_REF = "kefe.question_draft"
CANDIDATE_CASE_KIND = "CANDIDATE_CASE"
CANDIDATE_CASE_SCHEMA_REF = "kefe.candidate-case"
BUNDLE_SCHEMA_VERSION = "1.0.0"
BUNDLE_RISK_CODE = "UNREVIEWED_CANDIDATE_BUNDLE"

MAX_SLUG_CHARS = 120
MAX_TITLE_CHARS = 4096
MAX_SUMMARY_CHARS = 16_384
MAX_NOTE_CHARS = 16_384
MAX_CODE_CHARS = 128
MAX_OPTIONS = 8
MAX_COUNTRIES = 64
MAX_REVIEW_MODES = 16

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_LOCALE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
_COUNTRY = re.compile(r"^[A-Z]{2}$")
_SOURCE_ID_NAMESPACE = UUID("3b98348b-8a62-4cf7-83dc-99d5d1d2d4be")
_CONTEXT_ID_NAMESPACE = UUID("2e576ec8-bfc1-4b16-ae29-90099362cdaf")

_SEED_KEYS = frozenset(
    {
        "schema_ref",
        "schema_version",
        "source_brief_proposal_id",
        "source_brief_review_decision_id",
        "source_brief_payload_hash",
        "source_brief_normalized_artifact_id",
        "source_artifact_id",
        "source_content_hash",
        "evidence_ref",
        "headline",
        "synopsis",
        "source_url",
        "publisher_or_issuer",
        "published_at",
        "language_code",
        "jurisdiction_code",
        "editorial_configuration",
        "editorial_configuration_hash",
    }
)


def _fail(code: str) -> None:
    raise FinalStageError(code)


def _canonical_text(value: str, *, max_chars: int, field: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field} must be exact text")
    normalized = " ".join(value.split())
    if not normalized or normalized != value or len(value) > max_chars:
        raise ValueError(f"{field} must be canonical bounded text")
    return value


def _optional_text(value: str | None, *, max_chars: int, field: str) -> str | None:
    if value is None:
        return None
    return _canonical_text(value, max_chars=max_chars, field=field)


def _code(value: str, field: str) -> str:
    if type(value) is not str or len(value) > MAX_CODE_CHARS:
        raise ValueError(f"{field} is invalid")
    if _CODE.fullmatch(value) is None:
        raise ValueError(f"{field} must be an uppercase code")
    return value


def _http_url(value: str | None) -> str | None:
    if value is None:
        return None
    url = _canonical_text(value, max_chars=4096, field="source_url")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("source_url is invalid") from exc
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("source_url must use HTTP or HTTPS")
    if parsed.hostname is None or parsed.username is not None or parsed.password is not None:
        raise ValueError("source_url authority is invalid")
    if parsed.fragment or port not in (None, 80, 443):
        raise ValueError("source_url contains a forbidden component")
    return url


def _utc_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("published_at must be timezone-aware UTC")
    return value


def _uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    if type(value) is not str:
        _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise FinalStageError("CANDIDATE_SEED_ARTIFACT_INVALID") from exc
    if str(parsed) != value:
        _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
    return parsed


def _canonical_json_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


@dataclass(frozen=True, slots=True)
class CandidateCaseEditorialConfiguration:
    slug: str
    title: str
    summary: str
    base_format_code: str
    primary_domain_code: str
    content_risk: str
    issue_code: str
    issue_title: str
    question_stable_code: str
    question_prompt: str
    response_options: tuple[str, ...]
    flow_template_code: str
    flow_template_version_no: int
    content_locale: str
    market_scope: str
    country_codes: tuple[str, ...]
    required_review_modes: tuple[str, ...]
    is_fact_bearing: bool
    is_real_event: bool
    context_title: str
    cultural_context_note: str | None = None
    legal_context_note: str | None = None

    def __post_init__(self) -> None:
        if type(self.slug) is not str or len(self.slug) > MAX_SLUG_CHARS:
            raise ValueError("slug is invalid")
        if _SLUG.fullmatch(self.slug) is None:
            raise ValueError("slug must be lowercase kebab-case")
        for value, max_chars, field in (
            (self.title, MAX_TITLE_CHARS, "title"),
            (self.summary, MAX_SUMMARY_CHARS, "summary"),
            (self.issue_title, MAX_TITLE_CHARS, "issue_title"),
            (self.question_prompt, MAX_TITLE_CHARS, "question_prompt"),
            (self.context_title, MAX_TITLE_CHARS, "context_title"),
        ):
            _canonical_text(value, max_chars=max_chars, field=field)
        for value, field in (
            (self.base_format_code, "base_format_code"),
            (self.primary_domain_code, "primary_domain_code"),
            (self.content_risk, "content_risk"),
            (self.issue_code, "issue_code"),
            (self.question_stable_code, "question_stable_code"),
            (self.flow_template_code, "flow_template_code"),
        ):
            _code(value, field)
        if not 1 <= self.flow_template_version_no <= 1_000_000:
            raise ValueError("flow_template_version_no is outside the supported range")
        if _LOCALE.fullmatch(self.content_locale) is None:
            raise ValueError("content_locale is invalid")
        if type(self.market_scope) is not str or self.market_scope not in {
            "GLOBAL",
            "COUNTRY_SET",
        }:
            raise ValueError("market_scope is invalid")
        if type(self.is_fact_bearing) is not bool or type(self.is_real_event) is not bool:
            raise ValueError("fact and real-event flags must be exact booleans")
        if not 2 <= len(self.response_options) <= MAX_OPTIONS:
            raise ValueError("response_options must contain 2 to 8 values")
        if len(set(self.response_options)) != len(self.response_options):
            raise ValueError("response_options cannot contain duplicates")
        for option in self.response_options:
            _code(option, "response_option")
        if len(self.country_codes) > MAX_COUNTRIES:
            raise ValueError("country_codes exceed the supported range")
        if tuple(sorted(set(self.country_codes))) != self.country_codes:
            raise ValueError("country_codes must be sorted and unique")
        if any(_COUNTRY.fullmatch(item) is None for item in self.country_codes):
            raise ValueError("country_codes must be ISO alpha-2 codes")
        if self.market_scope == "GLOBAL" and self.country_codes:
            raise ValueError("GLOBAL market scope cannot contain country codes")
        if self.market_scope == "COUNTRY_SET" and not self.country_codes:
            raise ValueError("COUNTRY_SET market scope requires country codes")
        if not 1 <= len(self.required_review_modes) <= MAX_REVIEW_MODES:
            raise ValueError("required_review_modes are outside the supported range")
        if tuple(sorted(set(self.required_review_modes))) != self.required_review_modes:
            raise ValueError("required_review_modes must be sorted and unique")
        for mode in self.required_review_modes:
            _code(mode, "required_review_mode")
        if "EDITORIAL" not in self.required_review_modes:
            raise ValueError("required_review_modes must include EDITORIAL")
        _optional_text(
            self.cultural_context_note,
            max_chars=MAX_NOTE_CHARS,
            field="cultural_context_note",
        )
        _optional_text(
            self.legal_context_note,
            max_chars=MAX_NOTE_CHARS,
            field="legal_context_note",
        )

    def as_mapping(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "base_format_code": self.base_format_code,
            "primary_domain_code": self.primary_domain_code,
            "content_risk": self.content_risk,
            "issue_code": self.issue_code,
            "issue_title": self.issue_title,
            "question_stable_code": self.question_stable_code,
            "question_prompt": self.question_prompt,
            "response_options": list(self.response_options),
            "flow_template_code": self.flow_template_code,
            "flow_template_version_no": self.flow_template_version_no,
            "content_locale": self.content_locale,
            "market_scope": self.market_scope,
            "country_codes": list(self.country_codes),
            "required_review_modes": list(self.required_review_modes),
            "is_fact_bearing": self.is_fact_bearing,
            "is_real_event": self.is_real_event,
            "context_title": self.context_title,
            "cultural_context_note": self.cultural_context_note,
            "legal_context_note": self.legal_context_note,
        }

    @property
    def configuration_hash(self) -> str:
        return _canonical_json_hash(self.as_mapping())

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> CandidateCaseEditorialConfiguration:
        if type(value) is not dict:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        try:
            return cls(
                slug=value["slug"],
                title=value["title"],
                summary=value["summary"],
                base_format_code=value["base_format_code"],
                primary_domain_code=value["primary_domain_code"],
                content_risk=value["content_risk"],
                issue_code=value["issue_code"],
                issue_title=value["issue_title"],
                question_stable_code=value["question_stable_code"],
                question_prompt=value["question_prompt"],
                response_options=tuple(value["response_options"]),
                flow_template_code=value["flow_template_code"],
                flow_template_version_no=value["flow_template_version_no"],
                content_locale=value["content_locale"],
                market_scope=value["market_scope"],
                country_codes=tuple(value["country_codes"]),
                required_review_modes=tuple(value["required_review_modes"]),
                is_fact_bearing=value["is_fact_bearing"],
                is_real_event=value["is_real_event"],
                context_title=value["context_title"],
                cultural_context_note=value["cultural_context_note"],
                legal_context_note=value["legal_context_note"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FinalStageError("CANDIDATE_SEED_ARTIFACT_INVALID") from exc


@dataclass(frozen=True, slots=True)
class AcceptedSourceBriefCandidateSeed:
    source_brief_proposal_id: UUID
    source_brief_review_decision_id: UUID
    source_brief_payload_hash: str
    source_brief_normalized_artifact_id: UUID
    source_artifact_id: UUID
    source_content_hash: str
    evidence_ref: str
    headline: str
    synopsis: str | None
    source_url: str | None
    publisher_or_issuer: str | None
    published_at: datetime | None
    language_code: str | None
    jurisdiction_code: str | None
    editorial_configuration: CandidateCaseEditorialConfiguration

    def as_mapping(self) -> dict[str, Any]:
        config = self.editorial_configuration
        return {
            "schema_ref": SEED_SCHEMA_REF,
            "schema_version": SEED_SCHEMA_VERSION,
            "source_brief_proposal_id": str(self.source_brief_proposal_id),
            "source_brief_review_decision_id": str(self.source_brief_review_decision_id),
            "source_brief_payload_hash": self.source_brief_payload_hash,
            "source_brief_normalized_artifact_id": str(self.source_brief_normalized_artifact_id),
            "source_artifact_id": str(self.source_artifact_id),
            "source_content_hash": self.source_content_hash,
            "evidence_ref": self.evidence_ref,
            "headline": self.headline,
            "synopsis": self.synopsis,
            "source_url": self.source_url,
            "publisher_or_issuer": self.publisher_or_issuer,
            "published_at": (
                self.published_at.isoformat() if self.published_at is not None else None
            ),
            "language_code": self.language_code,
            "jurisdiction_code": self.jurisdiction_code,
            "editorial_configuration": config.as_mapping(),
            "editorial_configuration_hash": config.configuration_hash,
        }

    @property
    def content_hash(self) -> str:
        return _canonical_json_hash(self.as_mapping())

    @classmethod
    def from_artifact(cls, artifact: NormalizedArtifact) -> AcceptedSourceBriefCandidateSeed:
        if artifact.artifact_kind is not ArtifactKind.EXTERNAL_EVIDENCE:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        value = artifact.media_metadata
        if type(value) is not dict or frozenset(value) != _SEED_KEYS:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        if value["schema_ref"] != SEED_SCHEMA_REF:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        if value["schema_version"] != SEED_SCHEMA_VERSION:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        config = CandidateCaseEditorialConfiguration.from_mapping(value["editorial_configuration"])
        if value["editorial_configuration_hash"] != config.configuration_hash:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        try:
            published_at = (
                datetime.fromisoformat(value["published_at"])
                if value["published_at"] is not None
                else None
            )
            seed = cls(
                source_brief_proposal_id=_uuid(value["source_brief_proposal_id"]),
                source_brief_review_decision_id=_uuid(value["source_brief_review_decision_id"]),
                source_brief_payload_hash=value["source_brief_payload_hash"],
                source_brief_normalized_artifact_id=_uuid(
                    value["source_brief_normalized_artifact_id"]
                ),
                source_artifact_id=_uuid(value["source_artifact_id"]),
                source_content_hash=value["source_content_hash"],
                evidence_ref=value["evidence_ref"],
                headline=_canonical_text(
                    value["headline"],
                    max_chars=MAX_TITLE_CHARS,
                    field="headline",
                ),
                synopsis=_optional_text(
                    value["synopsis"],
                    max_chars=MAX_SUMMARY_CHARS,
                    field="synopsis",
                ),
                source_url=_http_url(value["source_url"]),
                publisher_or_issuer=_optional_text(
                    value["publisher_or_issuer"],
                    max_chars=MAX_TITLE_CHARS,
                    field="publisher_or_issuer",
                ),
                published_at=_utc_timestamp(published_at),
                language_code=_optional_text(
                    value["language_code"],
                    max_chars=35,
                    field="language_code",
                ),
                jurisdiction_code=_optional_text(
                    value["jurisdiction_code"],
                    max_chars=35,
                    field="jurisdiction_code",
                ),
                editorial_configuration=config,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FinalStageError("CANDIDATE_SEED_ARTIFACT_INVALID") from exc
        if seed.content_hash != artifact.content_hash:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        if seed.source_artifact_id != artifact.source_artifact_id:
            _fail("CANDIDATE_SEED_ARTIFACT_INVALID")
        return seed


class CandidateCaseBundleStageProcessor:
    def __init__(
        self,
        *,
        knowledge: KnowledgeRepository,
        repository: IngestionOrchestrationRepository,
    ) -> None:
        self._knowledge = knowledge
        self._repository = repository

    def process(
        self,
        *,
        run: IngestionRun,
        stage_code: str,
        stage_version: str,
        input_hash: str,
    ) -> StageProcessorResult:
        if stage_code != STAGE_CODE or stage_version != STAGE_VERSION:
            _fail("CANDIDATE_BUNDLE_STAGE_IDENTITY_INVALID")
        if run.pipeline_code != PIPELINE_CODE or run.pipeline_version != PIPELINE_VERSION:
            _fail("CANDIDATE_BUNDLE_PIPELINE_IDENTITY_INVALID")
        if run.input_artifact_kind is not InputArtifactKind.NORMALIZED_ARTIFACT:
            _fail("CANDIDATE_BUNDLE_INPUT_KIND_INVALID")
        if input_hash != run.input_content_hash:
            _fail("CANDIDATE_BUNDLE_INPUT_HASH_MISMATCH")

        artifact = self._knowledge.get_normalized_artifact(run.input_artifact_id)
        if artifact is None:
            _fail("CANDIDATE_SEED_ARTIFACT_NOT_FOUND")
        if artifact.content_hash != input_hash:
            _fail("CANDIDATE_BUNDLE_INPUT_HASH_MISMATCH")
        seed = AcceptedSourceBriefCandidateSeed.from_artifact(artifact)
        config = seed.editorial_configuration
        if run.configuration_hash != config.configuration_hash:
            _fail("CANDIDATE_BUNDLE_CONFIGURATION_INVALID")

        source_brief = self._repository.get_proposal(seed.source_brief_proposal_id)
        review = self._repository.get_review_decision(seed.source_brief_proposal_id)
        if source_brief is None or review is None:
            _fail("CANDIDATE_BUNDLE_SOURCE_BRIEF_NOT_FOUND")
        if (
            source_brief.proposal_kind != SOURCE_BRIEF_KIND
            or source_brief.payload_schema_ref != SOURCE_BRIEF_SCHEMA_REF
            or source_brief.payload_schema_version != SOURCE_BRIEF_SCHEMA_VERSION
            or source_brief.risk_code != SOURCE_BRIEF_RISK_CODE
            or source_brief.payload_hash != seed.source_brief_payload_hash
            or review.id != seed.source_brief_review_decision_id
            or review.decision is not ProposalReviewDecisionKind.ACCEPTED
        ):
            _fail("CANDIDATE_BUNDLE_SOURCE_BRIEF_INVALID")

        source_brief_artifact = self._knowledge.get_normalized_artifact(
            seed.source_brief_normalized_artifact_id
        )
        if source_brief_artifact is None:
            _fail("CANDIDATE_BUNDLE_SOURCE_BRIEF_INVALID")
        metadata = require_source_brief_normalized_artifact(source_brief_artifact)
        source = self._knowledge.get_source_artifact(seed.source_artifact_id)
        if source is None:
            _fail("CANDIDATE_BUNDLE_SOURCE_INVALID")
        if (
            metadata.source_artifact_id != seed.source_artifact_id
            or metadata.feed_content_hash != seed.source_content_hash
            or metadata.feed_storage_ref != seed.evidence_ref
            or source.content_hash != seed.source_content_hash
            or source.raw_storage_ref != seed.evidence_ref
        ):
            _fail("CANDIDATE_BUNDLE_SOURCE_INVALID")

        decision_id = uuid5(run.id, DECISION_PROBLEM_KIND)
        question_id = uuid5(run.id, QUESTION_DRAFT_KIND)
        source_ref_id = uuid5(_SOURCE_ID_NAMESPACE, str(run.id))
        context_id = uuid5(_CONTEXT_ID_NAMESPACE, str(run.id))
        context_body = seed.synopsis or config.summary
        source_locator = seed.source_url or seed.evidence_ref

        decision_payload = {
            "candidate_seed_artifact_id": str(artifact.id),
            "source_brief_proposal_id": str(seed.source_brief_proposal_id),
            "source_brief_review_decision_id": str(seed.source_brief_review_decision_id),
            "source_artifact_id": str(seed.source_artifact_id),
            "source_content_hash": seed.source_content_hash,
            "evidence_ref": seed.evidence_ref,
            "configuration_hash": config.configuration_hash,
            "issue_code": config.issue_code,
            "title": config.issue_title,
            "summary": config.summary,
            "primary_domain_code": config.primary_domain_code,
        }
        question_payload = {
            "candidate_seed_artifact_id": str(artifact.id),
            "source_brief_proposal_id": str(seed.source_brief_proposal_id),
            "source_brief_review_decision_id": str(seed.source_brief_review_decision_id),
            "configuration_hash": config.configuration_hash,
            "issue_code": config.issue_code,
            "stable_code": config.question_stable_code,
            "prompt": config.question_prompt,
            "response_type": "SINGLE_CHOICE",
            "response_schema": {"options": list(config.response_options)},
            "evidence_ref": seed.evidence_ref,
        }
        candidate_payload = {
            "candidate_seed_artifact_id": str(artifact.id),
            "source_brief_proposal_id": str(seed.source_brief_proposal_id),
            "source_brief_review_decision_id": str(seed.source_brief_review_decision_id),
            "source_artifact_id": str(seed.source_artifact_id),
            "source_content_hash": seed.source_content_hash,
            "evidence_ref": seed.evidence_ref,
            "configuration_hash": config.configuration_hash,
            "dependency_ids": [str(decision_id), str(question_id)],
            "slug": config.slug,
            "title": config.title,
            "summary": config.summary,
            "base_format_code": config.base_format_code,
            "primary_domain_code": config.primary_domain_code,
            "content_risk": config.content_risk,
            "content_locale": config.content_locale,
            "market_scope": config.market_scope,
            "country_codes": list(config.country_codes),
            "is_fact_bearing": config.is_fact_bearing,
            "is_real_event": config.is_real_event,
            "required_review_modes": list(config.required_review_modes),
            "flow_template_code": config.flow_template_code,
            "flow_template_version_no": config.flow_template_version_no,
            "cultural_context_note": config.cultural_context_note,
            "legal_context_note": config.legal_context_note,
            "issues": [
                {
                    "code": config.issue_code,
                    "title": config.issue_title,
                    "questions": [
                        {
                            "stable_code": config.question_stable_code,
                            "prompt": config.question_prompt,
                            "response_type": "SINGLE_CHOICE",
                            "response_schema": {"options": list(config.response_options)},
                            "is_active": True,
                            "is_required": True,
                            "sort_order": 0,
                        }
                    ],
                    "sort_order": 0,
                }
            ],
            "sources": [
                {
                    "id": str(source_ref_id),
                    "source_kind": "EXTERNAL_FEED",
                    "locator": source_locator,
                    "title": seed.headline,
                    "publisher": seed.publisher_or_issuer or "",
                    "published_at": (
                        seed.published_at.isoformat() if seed.published_at is not None else None
                    ),
                    "claim_status": "CLAIMED",
                    "verified": False,
                }
            ],
            "context_blocks": [
                {
                    "id": str(context_id),
                    "title": config.context_title,
                    "body": context_body,
                    "disclosure_level": "ESSENTIAL",
                    "claim_status": "CLAIMED",
                    "source_ids": [str(source_ref_id)],
                    "sort_order": 0,
                }
            ],
        }
        drafts = (
            ProposalDraft(
                proposal_kind=DECISION_PROBLEM_KIND,
                payload_schema_ref=DECISION_PROBLEM_SCHEMA_REF,
                payload_schema_version=BUNDLE_SCHEMA_VERSION,
                payload=decision_payload,
                configuration_version=config.configuration_hash,
                risk_code=BUNDLE_RISK_CODE,
                provenance_ref=seed.evidence_ref,
            ),
            ProposalDraft(
                proposal_kind=QUESTION_DRAFT_KIND,
                payload_schema_ref=QUESTION_DRAFT_SCHEMA_REF,
                payload_schema_version=BUNDLE_SCHEMA_VERSION,
                payload=question_payload,
                configuration_version=config.configuration_hash,
                risk_code=BUNDLE_RISK_CODE,
                provenance_ref=seed.evidence_ref,
            ),
            ProposalDraft(
                proposal_kind=CANDIDATE_CASE_KIND,
                payload_schema_ref=CANDIDATE_CASE_SCHEMA_REF,
                payload_schema_version=BUNDLE_SCHEMA_VERSION,
                payload=candidate_payload,
                configuration_version=config.configuration_hash,
                risk_code=BUNDLE_RISK_CODE,
                provenance_ref=seed.evidence_ref,
            ),
        )
        return StageProcessorResult(
            proposals=drafts,
            output_metadata={
                "candidate_seed_artifact_id": str(artifact.id),
                "source_brief_proposal_id": str(seed.source_brief_proposal_id),
                "configuration_hash": config.configuration_hash,
                "proposal_kinds": [
                    DECISION_PROBLEM_KIND,
                    QUESTION_DRAFT_KIND,
                    CANDIDATE_CASE_KIND,
                ],
            },
        )


__all__ = [
    "AcceptedSourceBriefCandidateSeed",
    "BUNDLE_RISK_CODE",
    "BUNDLE_SCHEMA_VERSION",
    "CANDIDATE_CASE_KIND",
    "CANDIDATE_CASE_SCHEMA_REF",
    "CandidateCaseBundleStageProcessor",
    "CandidateCaseEditorialConfiguration",
    "DECISION_PROBLEM_KIND",
    "DECISION_PROBLEM_SCHEMA_REF",
    "PIPELINE_CODE",
    "PIPELINE_VERSION",
    "QUESTION_DRAFT_KIND",
    "QUESTION_DRAFT_SCHEMA_REF",
    "SEED_SCHEMA_REF",
    "SEED_SCHEMA_VERSION",
    "STAGE_CODE",
    "STAGE_VERSION",
]

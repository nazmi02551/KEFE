from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringContextBlock,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
    MarketScope,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionProfile,
    EditorialProjectionRecord,
    EditorialProjectionResult,
    ReviewedProposal,
    ReviewedProposalBundle,
    stable_payload_hash,
)
from kefe_api.modules.editorial_projection.ports import (
    EditorialProjectionProfileRegistry,
    EditorialProjectionRepository,
    ReviewedProposalSource,
)


class EditorialProjectionService:
    def __init__(
        self,
        source: ReviewedProposalSource,
        profiles: EditorialProjectionProfileRegistry,
        repository: EditorialProjectionRepository,
    ) -> None:
        self._source = source
        self._profiles = profiles
        self._repository = repository

    def project(self, command: EditorialProjectionCommand) -> EditorialProjectionResult:
        profile = self._profiles.get(command.profile_code, command.profile_version)
        if profile is None:
            raise DomainError(
                "EDITORIAL_PROJECTION_PROFILE_NOT_FOUND",
                "Editorial projection profile not found",
                404,
            )

        bundle = self._source.get_bundle(
            command.candidate_proposal_id,
            command.proposal_review_decision_id,
        )
        if bundle is None:
            raise DomainError(
                "EDITORIAL_PROJECTION_SOURCE_NOT_FOUND",
                "Reviewed Candidate Case bundle not found",
                404,
            )

        self._validate_bundle(bundle, profile, command)
        input_hash = self._input_hash(bundle, profile, command)

        replay = self._repository.get_by_idempotency(
            command.candidate_proposal_id,
            command.idempotency_key,
        )
        if replay is not None:
            if replay.input_hash != input_hash:
                raise DomainError(
                    "EDITORIAL_PROJECTION_IDEMPOTENCY_CONFLICT",
                    "Idempotency key was already used with different projection input",
                    409,
                )
            return EditorialProjectionResult(record=replay, replayed=True)

        previous = self._repository.get_by_candidate(command.candidate_proposal_id)
        if previous is not None:
            raise DomainError(
                "EDITORIAL_PROJECTION_CANDIDATE_ALREADY_PROJECTED",
                "Candidate Case was already projected",
                409,
                meta={
                    "authoring_case_id": str(previous.authoring_case_id),
                    "authoring_case_version_id": str(
                        previous.authoring_case_version_id
                    ),
                },
            )

        identity, draft = self._map_draft(bundle.candidate, profile, command)
        created_at = datetime.now(UTC)
        audit = LifecycleAuditEntry.create(
            version=draft,
            actor_ref=command.requested_by_admin_ref,
            command="project_candidate_case",
            previous_state=None,
            new_state=ContentLifecycle.DRAFT,
            rationale=(
                f"Projected Candidate Case using {profile.profile_code} "
                f"v{profile.profile_version}"
            ),
            occurred_at=created_at,
        )
        record = EditorialProjectionRecord(
            id=uuid4(),
            candidate_proposal_id=bundle.candidate.id,
            proposal_review_decision_id=bundle.candidate.review_decision_id,
            profile_code=profile.profile_code,
            profile_version=profile.profile_version,
            idempotency_key=command.idempotency_key,
            requested_by_admin_ref=command.requested_by_admin_ref,
            input_hash=input_hash,
            authoring_case_id=identity.id,
            authoring_case_version_id=draft.id,
            created_at=created_at,
        )
        try:
            self._repository.create_atomically(
                identity=identity,
                initial_version=draft,
                audit=audit,
                record=record,
            )
        except ValueError as exc:
            raise DomainError(
                "EDITORIAL_PROJECTION_PERSISTENCE_CONFLICT",
                "Editorial projection conflicted with existing state",
                409,
                detail=str(exc),
            ) from exc
        return EditorialProjectionResult(record=record, replayed=False)

    @staticmethod
    def _validate_bundle(
        bundle: ReviewedProposalBundle,
        profile: EditorialProjectionProfile,
        command: EditorialProjectionCommand,
    ) -> None:
        candidate = bundle.candidate
        if candidate.id != command.candidate_proposal_id:
            raise DomainError(
                "EDITORIAL_PROJECTION_SOURCE_MISMATCH",
                "Candidate proposal identity does not match command",
                422,
            )
        if candidate.review_decision_id != command.proposal_review_decision_id:
            raise DomainError(
                "EDITORIAL_PROJECTION_REVIEW_MISMATCH",
                "Proposal review decision does not match command",
                422,
            )
        if candidate.proposal_kind != "CANDIDATE_CASE":
            raise DomainError(
                "EDITORIAL_PROJECTION_SOURCE_KIND_INVALID",
                "Projection requires a CANDIDATE_CASE proposal",
                422,
            )
        if candidate.review_decision != "ACCEPTED":
            raise DomainError(
                "EDITORIAL_PROJECTION_SOURCE_NOT_ACCEPTED",
                "Candidate Case must have a terminal ACCEPTED review decision",
                422,
            )
        if (
            candidate.payload_schema_ref != profile.candidate_schema_ref
            or candidate.payload_schema_version != profile.candidate_schema_version
        ):
            raise DomainError(
                "EDITORIAL_PROJECTION_PROFILE_SCHEMA_INCOMPATIBLE",
                "Candidate Case schema is incompatible with projection profile",
                422,
            )

        dependency_map = bundle.dependency_map()
        missing = [
            str(dependency_id)
            for dependency_id in candidate.dependency_ids
            if dependency_id not in dependency_map
        ]
        if missing:
            raise DomainError(
                "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY",
                "Candidate Case dependencies are missing",
                422,
                meta={"missing_dependency_ids": missing},
            )
        rejected = [
            str(item.id)
            for item in bundle.dependencies
            if item.id in candidate.dependency_ids and item.review_decision != "ACCEPTED"
        ]
        if rejected:
            raise DomainError(
                "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY",
                "Candidate Case dependencies are not ACCEPTED",
                422,
                meta={"unaccepted_dependency_ids": rejected},
            )
        dependency_kinds = {
            item.proposal_kind
            for item in bundle.dependencies
            if item.id in candidate.dependency_ids
        }
        missing_kinds = sorted(profile.required_dependency_kinds - dependency_kinds)
        if missing_kinds:
            raise DomainError(
                "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY",
                "Projection profile requires additional accepted dependency kinds",
                422,
                meta={"missing_dependency_kinds": missing_kinds},
            )

    @staticmethod
    def _input_hash(
        bundle: ReviewedProposalBundle,
        profile: EditorialProjectionProfile,
        command: EditorialProjectionCommand,
    ) -> str:
        return stable_payload_hash(
            {
                "candidate_id": str(bundle.candidate.id),
                "candidate_payload_hash": bundle.candidate.payload_hash,
                "review_decision_id": str(bundle.candidate.review_decision_id),
                "dependencies": [
                    {
                        "id": str(item.id),
                        "kind": item.proposal_kind,
                        "payload_hash": item.payload_hash,
                        "review_decision_id": str(item.review_decision_id),
                        "review_decision": item.review_decision,
                    }
                    for item in sorted(bundle.dependencies, key=lambda item: str(item.id))
                ],
                "profile_code": profile.profile_code,
                "profile_version": profile.profile_version,
                "explicit_flow_template_code": command.explicit_flow_template_code,
                "explicit_flow_template_version": command.explicit_flow_template_version,
            }
        )

    def _map_draft(
        self,
        candidate: ReviewedProposal,
        profile: EditorialProjectionProfile,
        command: EditorialProjectionCommand,
    ) -> tuple[CaseIdentity, AuthoringCaseVersion]:
        payload = candidate.payload
        required = (
            "slug",
            "title",
            "summary",
            "base_format_code",
            "primary_domain_code",
            "content_risk",
            "issues",
        )
        missing = [name for name in required if not payload.get(name)]
        if missing:
            raise DomainError(
                "EDITORIAL_PROJECTION_REQUIRED_AUTHORING_FIELD_MISSING",
                "Candidate Case is missing required authoring fields",
                422,
                meta={"missing_fields": missing},
            )

        flow_code, flow_version = self._resolve_flow(payload, profile, command)
        case_id = uuid4()
        identity = CaseIdentity(id=case_id, slug=str(payload["slug"]).strip())
        issues = self._map_issues(payload["issues"])
        sources = self._map_sources(payload.get("sources", []))
        context_blocks = self._map_context_blocks(
            payload.get("context_blocks", []), sources
        )
        country_codes = tuple(str(item) for item in payload.get("country_codes", []))
        market_scope = MarketScope(payload.get("market_scope", "GLOBAL"))
        draft = AuthoringCaseVersion(
            id=uuid4(),
            case_id=case_id,
            version_no=1,
            state=ContentLifecycle.DRAFT,
            title=str(payload["title"]).strip(),
            summary=str(payload["summary"]).strip(),
            base_format_code=str(payload["base_format_code"]).strip(),
            primary_domain_code=str(payload["primary_domain_code"]).strip(),
            content_risk=str(payload["content_risk"]).strip(),
            issues=issues,
            context_blocks=context_blocks,
            sources=sources,
            modifiers=tuple(str(item) for item in payload.get("modifiers", [])),
            is_fact_bearing=bool(payload.get("is_fact_bearing", False)),
            is_real_event=bool(payload.get("is_real_event", False)),
            required_review_modes=tuple(
                str(item) for item in payload.get("required_review_modes", [])
            ),
            completed_review_modes=(),
            flow_template_code=flow_code,
            flow_template_version_no=flow_version,
            content_locale=str(payload.get("content_locale", "tr-TR")),
            market_scope=market_scope,
            country_codes=country_codes,
            cultural_context_note=payload.get("cultural_context_note"),
            legal_context_note=payload.get("legal_context_note"),
        )
        return identity, draft

    @staticmethod
    def _resolve_flow(
        payload: dict[str, Any],
        profile: EditorialProjectionProfile,
        command: EditorialProjectionCommand,
    ) -> tuple[str, int]:
        if command.explicit_flow_template_code is not None:
            if not profile.allow_command_flow_selection:
                raise DomainError(
                    "EDITORIAL_PROJECTION_FLOW_REFERENCE_INVALID",
                    "Projection profile does not allow command Flow selection",
                    422,
                )
            assert command.explicit_flow_template_version is not None
            return (
                command.explicit_flow_template_code,
                command.explicit_flow_template_version,
            )
        code = payload.get("flow_template_code")
        version = payload.get("flow_template_version_no")
        if code is not None or version is not None:
            if not profile.allow_candidate_flow_selection or not code or not version:
                raise DomainError(
                    "EDITORIAL_PROJECTION_FLOW_REFERENCE_INVALID",
                    "Candidate Flow selection is incomplete or not allowed",
                    422,
                )
            return str(code), int(version)
        raise DomainError(
            "EDITORIAL_PROJECTION_FLOW_REFERENCE_INVALID",
            "Explicit versioned Flow selection is required",
            422,
        )

    @staticmethod
    def _map_issues(raw_issues: Any) -> tuple[AuthoringIssue, ...]:
        if not isinstance(raw_issues, list) or not raw_issues:
            raise DomainError(
                "EDITORIAL_PROJECTION_REQUIRED_AUTHORING_FIELD_MISSING",
                "At least one Issue is required",
                422,
            )
        issues: list[AuthoringIssue] = []
        for issue_index, raw_issue in enumerate(raw_issues):
            questions_raw = raw_issue.get("questions", [])
            if not questions_raw:
                raise DomainError(
                    "EDITORIAL_PROJECTION_REQUIRED_AUTHORING_FIELD_MISSING",
                    "Each Issue requires at least one Question",
                    422,
                    meta={"issue_index": issue_index},
                )
            questions = tuple(
                AuthoringQuestion(
                    id=uuid4(),
                    stable_code=str(question["stable_code"]),
                    prompt=str(question["prompt"]),
                    response_type=str(question["response_type"]),
                    response_schema=dict(question.get("response_schema", {})),
                    is_active=bool(question.get("is_active", True)),
                    is_required=bool(question.get("is_required", True)),
                    sort_order=int(question.get("sort_order", question_index)),
                )
                for question_index, question in enumerate(questions_raw)
            )
            issues.append(
                AuthoringIssue(
                    id=uuid4(),
                    code=str(raw_issue["code"]),
                    title=str(raw_issue["title"]),
                    questions=questions,
                    sort_order=int(raw_issue.get("sort_order", issue_index)),
                )
            )
        return tuple(issues)

    @staticmethod
    def _map_sources(raw_sources: Any) -> tuple[AuthoringSourceReference, ...]:
        return tuple(
            AuthoringSourceReference(
                id=UUID(str(item["id"])) if item.get("id") else uuid4(),
                source_kind=str(item["source_kind"]),
                locator=str(item["locator"]),
                title=str(item["title"]),
                publisher=str(item.get("publisher", "")),
                published_at=(
                    datetime.fromisoformat(str(item["published_at"]))
                    if item.get("published_at")
                    else None
                ),
                claim_status=item.get("claim_status"),
                verified=bool(item.get("verified", False)),
            )
            for item in raw_sources
        )

    @staticmethod
    def _map_context_blocks(
        raw_blocks: Any,
        sources: tuple[AuthoringSourceReference, ...],
    ) -> tuple[AuthoringContextBlock, ...]:
        known_source_ids = {item.id for item in sources}
        blocks: list[AuthoringContextBlock] = []
        for index, item in enumerate(raw_blocks):
            source_ids = tuple(UUID(str(value)) for value in item.get("source_ids", []))
            unknown = [str(value) for value in source_ids if value not in known_source_ids]
            if unknown:
                raise DomainError(
                    "EDITORIAL_PROJECTION_SOURCE_REFERENCE_INVALID",
                    "Context block references an unknown source",
                    422,
                    meta={"unknown_source_ids": unknown},
                )
            blocks.append(
                AuthoringContextBlock(
                    id=UUID(str(item["id"])) if item.get("id") else uuid4(),
                    title=str(item["title"]),
                    body=str(item["body"]),
                    disclosure_level=str(item["disclosure_level"]),
                    claim_status=str(item["claim_status"]),
                    source_ids=source_ids,
                    sort_order=int(item.get("sort_order", index)),
                    block_type=str(item.get("block_type", "CONTEXT")),
                )
            )
        return tuple(blocks)

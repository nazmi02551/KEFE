from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.lineage_models import (
    LineageSnapshot,
    RevisionCommitStatus,
    RevisionDraft,
)
from kefe_api.modules.decision.models import CaseVersion, FlowStep, Question, WeighState
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.flow_runtime.models import FlowStepRuntimeState
from kefe_api.modules.flow_runtime.service import FlowRuntimeService


class DecisionLineageService:
    def __init__(
        self,
        repository: DecisionRepository,
        flow_runtime: FlowRuntimeService,
    ) -> None:
        self._repo = repository
        self._flow_runtime = flow_runtime

    def update_revision_responses(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        responses: dict[UUID, Any],
    ) -> RevisionDraft:
        session, case, step = self._later_decision_step(
            actor_id=actor_id,
            session_id=session_id,
            flow_step_code=flow_step_code,
            require_ready=True,
        )
        del session, step
        questions = {question.id: question for question in case.questions}
        unknown = [str(question_id) for question_id in responses if question_id not in questions]
        if unknown:
            raise DomainError(
                "REVISION_RESPONSE_INVALID",
                "Revision response contains unknown questions",
                422,
                meta={"unknown_question_ids": unknown},
            )
        invalid = [
            {
                "question_id": str(question_id),
                "response_type": questions[question_id].response_type,
            }
            for question_id, value in responses.items()
            if not self._is_valid_response(questions[question_id], value)
        ]
        if invalid:
            raise DomainError(
                "REVISION_RESPONSE_INVALID",
                "Revision response does not match the question schema",
                422,
                meta={"invalid_responses": invalid},
            )
        current = self._repo.get_revision_draft(
            session_id=session_id, flow_step_code=flow_step_code
        )
        merged = dict(current.responses) if current else {}
        merged.update(responses)
        draft = RevisionDraft(
            session_id=session_id,
            flow_step_code=flow_step_code,
            responses=merged,
            reason_snapshot=current.reason_snapshot if current else None,
            updated_at=datetime.now(UTC),
        )
        self._repo.save_revision_draft(draft)
        return draft

    def update_revision_reason(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        tags: list[str],
        text: str | None,
    ) -> RevisionDraft:
        _, case, _ = self._later_decision_step(
            actor_id=actor_id,
            session_id=session_id,
            flow_step_code=flow_step_code,
            require_ready=True,
        )
        policy = self._reason_policy(case.questions)
        if policy is None:
            raise DomainError(
                "REASON_NOT_SUPPORTED",
                "This Case does not accept a structured reason",
                422,
            )
        reason_snapshot = self._normalize_reason(policy=policy, tags=tags, text=text)
        current = self._repo.get_revision_draft(
            session_id=session_id, flow_step_code=flow_step_code
        )
        draft = RevisionDraft(
            session_id=session_id,
            flow_step_code=flow_step_code,
            responses=dict(current.responses) if current else {},
            reason_snapshot=reason_snapshot,
            updated_at=datetime.now(UTC),
        )
        self._repo.save_revision_draft(draft)
        return draft

    def record_flow_step_exposure(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
    ):
        session = self._owned_session(actor_id, session_id)
        case = self._case(session.case_version_id)
        step = self._flow_step(case, flow_step_code)
        if step.primitive_code != "CONTEXT":
            raise DomainError(
                "EXPOSURE_STEP_UNSUPPORTED",
                "Explicit v1 exposure recording is limited to Context Flow Steps",
                422,
            )
        runtime = self._flow_runtime.get_runtime(actor_id=actor_id, session_id=session_id)
        runtime_step = next((item for item in runtime.steps if item.code == flow_step_code), None)
        if runtime_step is None:
            raise DomainError("FLOW_STEP_NOT_FOUND", "Flow Step not found", 404)
        if runtime_step.state not in {
            FlowStepRuntimeState.READY,
            FlowStepRuntimeState.COMPLETED,
        }:
            raise DomainError(
                "FLOW_STEP_NOT_READY",
                "Flow Step is not ready for exposure",
                409,
                meta={"state": runtime_step.state.value},
            )

        between_decisions = self._context_between_decisions(case, flow_step_code)
        return self._repo.record_exposure(
            actor_id=actor_id,
            session_id=session_id,
            case_version_id=session.case_version_id,
            flow_step_code=flow_step_code,
            resource_category="CONTEXT",
            resource_ref=None,
            primitive_code=step.primitive_code,
            capability_codes=step.capability_codes,
            metadata={"source": "FLOW_STEP_ENCOUNTER"},
            idempotency_key=idempotency_key,
            occurred_at=datetime.now(UTC),
            intervention_type_code=(
                "CONTEXT_REVEAL" if between_decisions and session.state is WeighState.COMMITTED else None
            ),
            intervention_metadata=(
                {"flow_step_code": flow_step_code, "trigger": "BETWEEN_DECISIONS"}
                if between_decisions and session.state is WeighState.COMMITTED
                else None
            ),
        )

    def commit_revision(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
    ):
        _, case, _ = self._later_decision_step(
            actor_id=actor_id,
            session_id=session_id,
            flow_step_code=flow_step_code,
            require_ready=True,
        )
        attempt = self._repo.commit_revision(
            actor_id=actor_id,
            session_id=session_id,
            flow_step_code=flow_step_code,
            idempotency_key=idempotency_key,
            required_question_ids=frozenset(
                question.id for question in case.questions if question.required
            ),
            committed_at=datetime.now(UTC),
        )
        if attempt.status in {
            RevisionCommitStatus.COMMITTED,
            RevisionCommitStatus.IDEMPOTENT_REPLAY,
        }:
            assert attempt.revision is not None
            return attempt
        if attempt.status is RevisionCommitStatus.NOT_FOUND:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if attempt.status is RevisionCommitStatus.ALREADY_COMMITTED:
            raise DomainError(
                "DECISION_REVISION_ALREADY_COMMITTED",
                "Decision revision for this Flow Step is already committed",
                409,
            )
        if attempt.status is RevisionCommitStatus.INCOMPLETE:
            raise DomainError(
                "REVISION_RESPONSE_INCOMPLETE",
                "Required revision responses are missing",
                422,
                meta={
                    "missing_question_ids": [
                        str(question_id) for question_id in attempt.missing_question_ids
                    ]
                },
            )
        if attempt.status is RevisionCommitStatus.IDEMPOTENCY_KEY_REUSED:
            raise DomainError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key was already used for another revision commit",
                409,
            )
        raise RuntimeError(f"Unsupported revision commit status: {attempt.status}")

    def lineage(self, *, actor_id: UUID, session_id: UUID) -> LineageSnapshot:
        session = self._owned_session(actor_id, session_id)
        return LineageSnapshot(
            session_id=session.id,
            case_version_id=session.case_version_id,
            revisions=self._repo.list_decision_revisions(session.id),
            exposures=self._repo.list_exposures(session.id),
            interventions=self._repo.list_interventions(session.id),
            deltas=self._repo.list_decision_deltas(session.id),
        )

    def _later_decision_step(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        require_ready: bool,
    ) -> tuple[Any, CaseVersion, FlowStep]:
        session = self._owned_session(actor_id, session_id)
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "REVISION_INITIAL_COMMIT_REQUIRED",
                "Initial Commit is required before a later Decision revision",
                409,
            )
        case = self._case(session.case_version_id)
        step = self._flow_step(case, flow_step_code)
        if step.primitive_code != "DECISION":
            raise DomainError(
                "REVISION_STEP_INVALID",
                "Requested Flow Step is not a Decision Step",
                422,
            )
        first_decision = next(
            (
                item.code
                for item in case.resolved_flow.steps
                if item.primitive_code == "DECISION"
            ),
            None,
        )
        if flow_step_code == first_decision:
            raise DomainError(
                "REVISION_STEP_INVALID",
                "Initial Decision Step is committed through the initial Commit endpoint",
                422,
            )
        if require_ready:
            runtime = self._flow_runtime.get_runtime(actor_id=actor_id, session_id=session_id)
            runtime_step = next((item for item in runtime.steps if item.code == flow_step_code), None)
            if runtime_step is None:
                raise DomainError("FLOW_STEP_NOT_FOUND", "Flow Step not found", 404)
            if runtime_step.state is FlowStepRuntimeState.COMPLETED:
                raise DomainError(
                    "DECISION_REVISION_ALREADY_COMMITTED",
                    "Decision revision for this Flow Step is already committed",
                    409,
                )
            if runtime_step.state is not FlowStepRuntimeState.READY:
                raise DomainError(
                    "FLOW_STEP_NOT_READY",
                    "Decision Flow Step is not ready",
                    409,
                    meta={"state": runtime_step.state.value},
                )
        return session, case, step

    def _owned_session(self, actor_id: UUID, session_id: UUID):
        session = self._repo.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        return session

    def _case(self, case_version_id: UUID) -> CaseVersion:
        case = self._repo.get_case_version(case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)
        if case.resolved_flow is None:
            raise DomainError(
                "FLOW_RUNTIME_UNAVAILABLE",
                "CaseVersion does not contain a pinned resolved Flow",
                409,
            )
        return case

    @staticmethod
    def _flow_step(case: CaseVersion, flow_step_code: str) -> FlowStep:
        assert case.resolved_flow is not None
        step = next((item for item in case.resolved_flow.steps if item.code == flow_step_code), None)
        if step is None:
            raise DomainError("FLOW_STEP_NOT_FOUND", "Flow Step not found", 404)
        return step

    @staticmethod
    def _context_between_decisions(case: CaseVersion, flow_step_code: str) -> bool:
        assert case.resolved_flow is not None
        step_by_code = {item.code: item for item in case.resolved_flow.steps}
        predecessors: dict[str, set[str]] = {code: set() for code in step_by_code}
        for step in case.resolved_flow.steps:
            for next_code in step.next_step_codes:
                if next_code in predecessors:
                    predecessors[next_code].add(step.code)

        pending = list(predecessors.get(flow_step_code, set()))
        seen: set[str] = set()
        has_before = False
        while pending:
            code = pending.pop()
            if code in seen:
                continue
            seen.add(code)
            step = step_by_code.get(code)
            if step is not None and step.primitive_code == "DECISION":
                has_before = True
                break
            pending.extend(predecessors.get(code, set()))

        current = step_by_code.get(flow_step_code)
        pending = list(current.next_step_codes) if current else []
        seen.clear()
        has_after = False
        while pending:
            code = pending.pop()
            if code in seen:
                continue
            seen.add(code)
            step = step_by_code.get(code)
            if step is None:
                continue
            if step.primitive_code == "DECISION":
                has_after = True
                break
            pending.extend(step.next_step_codes)
        return has_before and has_after

    @staticmethod
    def _reason_policy(questions: tuple[Question, ...]) -> Mapping[str, Any] | None:
        for question in questions:
            raw = question.response_schema.get("reason")
            if isinstance(raw, Mapping):
                return raw
        return None

    @classmethod
    def _normalize_reason(
        cls,
        *,
        policy: Mapping[str, Any],
        tags: list[str],
        text: str | None,
    ) -> dict[str, Any]:
        normalized_tags = tuple(dict.fromkeys(tag.strip().upper() for tag in tags if tag.strip()))
        normalized_text = text.strip() if text is not None else None
        if normalized_text == "":
            normalized_text = None
        if not normalized_tags and normalized_text is None:
            raise DomainError("REASON_EMPTY", "At least one reason tag or short text is required", 422)
        allowed_tags = {
            str(tag).strip().upper()
            for tag in policy.get("tags", ())
            if str(tag).strip()
        }
        unknown_tags = [tag for tag in normalized_tags if tag not in allowed_tags]
        if unknown_tags:
            raise DomainError(
                "REASON_TAG_INVALID",
                "Reason contains unsupported tags",
                422,
                meta={"unknown_tags": unknown_tags},
            )
        max_tags = cls._bounded_int(policy.get("max_tags", 3), default=3, minimum=1, maximum=10)
        if len(normalized_tags) > max_tags:
            raise DomainError(
                "REASON_TAG_LIMIT_EXCEEDED",
                "Too many reason tags",
                422,
                meta={"max_tags": max_tags},
            )
        text_enabled = policy.get("text_enabled", False) is True
        if normalized_text is not None and not text_enabled:
            raise DomainError("REASON_TEXT_NOT_ALLOWED", "Short reason text is disabled for this Case", 422)
        text_max_length = cls._bounded_int(
            policy.get("text_max_length", 500), default=500, minimum=1, maximum=1000
        )
        if normalized_text is not None and len(normalized_text) > text_max_length:
            raise DomainError(
                "REASON_TEXT_TOO_LONG",
                "Short reason text exceeds the Case limit",
                422,
                meta={"max_length": text_max_length},
            )
        return {
            "tags": list(normalized_tags),
            "text": normalized_text,
            "moderation_state": "PENDING" if normalized_text is not None else "NOT_REQUIRED",
            "visibility": "PRIVATE",
        }

    @staticmethod
    def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            return default
        return min(max(value, minimum), maximum)

    @staticmethod
    def _is_valid_response(question: Question, value: Any) -> bool:
        if question.response_type == "SINGLE_CHOICE":
            return isinstance(value, str) and value in question.options
        if question.response_type == "CONFIDENCE":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            minimum = question.response_schema.get("min", 1)
            maximum = question.response_schema.get("max", 10)
            step = question.response_schema.get("step", 1)
            if not all(isinstance(item, (int, float)) for item in (minimum, maximum, step)):
                return False
            if step <= 0 or value < minimum or value > maximum:
                return False
            steps = (value - minimum) / step
            return abs(steps - round(steps)) < 1e-9
        return False

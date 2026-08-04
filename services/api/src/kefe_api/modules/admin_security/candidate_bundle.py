from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid5

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.admin_security.source_brief_review import (
    SecuredSourceBriefReviewService,
)
from kefe_api.modules.ingestion_orchestration.candidate_case_bundle import (
    BUNDLE_RISK_CODE,
    BUNDLE_SCHEMA_VERSION,
    CANDIDATE_CASE_KIND,
    DECISION_PROBLEM_KIND,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    QUESTION_DRAFT_KIND,
    SEED_SCHEMA_VERSION,
    STAGE_CODE,
    STAGE_VERSION,
    AcceptedSourceBriefCandidateSeed,
    CandidateCaseBundleStageProcessor,
    CandidateCaseEditorialConfiguration,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    FinalStageError,
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import ArtifactKind, NormalizedArtifact
from kefe_api.modules.knowledge.ports import KnowledgeRepository

_SEED_NAMESPACE = UUID("a4c8f1f4-10f9-4bc0-aa32-6e8ad6b4688d")
_STAGE_NAMESPACE = UUID("6ab17f0c-72f6-4458-a882-058403fcffb4")
_EXPECTED_KINDS = (
    DECISION_PROBLEM_KIND,
    QUESTION_DRAFT_KIND,
    CANDIDATE_CASE_KIND,
)


def _error(code: str, message: str, status: int = 409) -> DomainError:
    return DomainError(code, message, status)


class CandidateBundleResult:
    __slots__ = (
        "candidate_seed_artifact_id",
        "run_id",
        "proposal_ids",
        "run_state",
    )

    def __init__(
        self,
        *,
        candidate_seed_artifact_id: UUID,
        run_id: UUID,
        proposal_ids: tuple[UUID, UUID, UUID],
        run_state: IngestionRunState,
    ) -> None:
        self.candidate_seed_artifact_id = candidate_seed_artifact_id
        self.run_id = run_id
        self.proposal_ids = proposal_ids
        self.run_state = run_state


class SecuredCandidateBundleService:
    def __init__(
        self,
        *,
        security: AdminSecurityService,
        source_briefs: SecuredSourceBriefReviewService,
        ingestion: IngestionOrchestrationService,
        repository: IngestionOrchestrationRepository,
        knowledge: KnowledgeRepository,
        processor: CandidateCaseBundleStageProcessor,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._security = security
        self._source_briefs = source_briefs
        self._ingestion = ingestion
        self._repository = repository
        self._knowledge = knowledge
        self._processor = processor
        self._clock = clock

    def build(
        self,
        principal: AdminPrincipal,
        *,
        source_brief_proposal_id: UUID,
        source_brief_review_decision_id: UUID,
        configuration: CandidateCaseEditorialConfiguration,
    ) -> CandidateBundleResult:
        self._security.authorize(principal, AdminCapability.SOURCE_VERIFY)
        record = self._source_briefs.detail(principal, source_brief_proposal_id)
        review = record.queue_record.review
        if (
            review is None
            or review.id != source_brief_review_decision_id
            or review.decision is not ProposalReviewDecisionKind.ACCEPTED
        ):
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_SOURCE_BRIEF_REVIEW_REQUIRED",
                "Source Brief must have the exact ACCEPTED review decision",
            )

        seed = AcceptedSourceBriefCandidateSeed(
            source_brief_proposal_id=record.queue_record.proposal.id,
            source_brief_review_decision_id=review.id,
            source_brief_payload_hash=record.queue_record.proposal.payload_hash,
            source_brief_normalized_artifact_id=record.payload.normalized_artifact_id,
            source_artifact_id=record.payload.source_artifact_id,
            source_content_hash=record.payload.source_content_hash,
            evidence_ref=record.payload.evidence_ref,
            headline=record.payload.headline,
            synopsis=record.payload.synopsis,
            source_url=record.payload.source_url,
            publisher_or_issuer=record.payload.publisher_or_issuer,
            published_at=record.payload.published_at,
            language_code=record.payload.language_code,
            jurisdiction_code=record.payload.jurisdiction_code,
            editorial_configuration=configuration,
        )
        artifact = self._seed_artifact(seed, review.decided_at)
        run = self._ingestion.start_run(
            input_artifact_kind=InputArtifactKind.NORMALIZED_ARTIFACT,
            input_artifact_id=artifact.id,
            input_content_hash=artifact.content_hash,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=configuration.configuration_hash,
            locale=configuration.content_locale,
            jurisdiction_code=record.payload.jurisdiction_code,
        )
        completed, proposals = self._execute(run)
        ids = tuple(proposal.id for proposal in proposals)
        assert len(ids) == 3
        return CandidateBundleResult(
            candidate_seed_artifact_id=artifact.id,
            run_id=completed.id,
            proposal_ids=(ids[0], ids[1], ids[2]),
            run_state=completed.state,
        )

    def _seed_artifact(
        self,
        seed: AcceptedSourceBriefCandidateSeed,
        decided_at: datetime,
    ) -> NormalizedArtifact:
        configuration = seed.editorial_configuration
        artifact_id = uuid5(
            _SEED_NAMESPACE,
            (
                f"{seed.source_brief_proposal_id}:"
                f"{seed.source_brief_review_decision_id}:"
                f"{configuration.configuration_hash}:{SEED_SCHEMA_VERSION}"
            ),
        )
        artifact = NormalizedArtifact(
            id=artifact_id,
            source_artifact_id=seed.source_artifact_id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=decided_at,
            content_hash=seed.content_hash,
            text=configuration.summary,
            language_code=seed.language_code,
            jurisdiction_code=seed.jurisdiction_code,
            media_metadata=seed.as_mapping(),
        )
        existing = self._knowledge.get_normalized_artifact(artifact.id)
        if existing is not None:
            if existing != artifact:
                raise _error(
                    "ADMIN_CANDIDATE_BUNDLE_SEED_CONFLICT",
                    "Candidate bundle seed identity conflicts with existing content",
                )
            return existing
        try:
            self._knowledge.add_normalized_artifact(artifact)
        except ValueError as exc:
            existing = self._knowledge.get_normalized_artifact(artifact.id)
            if existing == artifact:
                return artifact
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_SEED_CONFLICT",
                "Candidate bundle seed could not be persisted exactly",
            ) from exc
        return artifact

    def _execute(
        self,
        run: IngestionRun,
    ) -> tuple[IngestionRun, tuple[Proposal, Proposal, Proposal]]:
        stage_id = uuid5(
            _STAGE_NAMESPACE,
            f"{run.id}:{STAGE_CODE}:{STAGE_VERSION}:1",
        )
        proposal_ids = tuple(uuid5(run.id, kind) for kind in _EXPECTED_KINDS)
        recovered = self._recover(
            run=run,
            stage_id=stage_id,
            proposal_ids=proposal_ids,
        )
        if recovered is not None:
            return recovered

        current = self._repository.get_run(run.id)
        if current is None:
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle ingestion run is missing",
            )
        if current.state is IngestionRunState.QUEUED:
            current = current.transition(IngestionRunState.RUNNING, at=self._clock())
            self._repository.update_run(current)
        elif current.state is not IngestionRunState.RUNNING:
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle ingestion run is not executable",
            )

        started_at = self._clock()
        try:
            result = self._processor.process(
                run=current,
                stage_code=STAGE_CODE,
                stage_version=STAGE_VERSION,
                input_hash=current.input_content_hash,
            )
        except FinalStageError as exc:
            failed = StageExecution(
                id=stage_id,
                run_id=current.id,
                stage_code=STAGE_CODE,
                stage_version=STAGE_VERSION,
                attempt_no=1,
                max_attempts=1,
                executor_kind=ExecutorKind.DETERMINISTIC,
                input_hash=current.input_content_hash,
                started_at=started_at,
                completed_at=self._clock(),
                outcome=StageOutcome.FAILED_FINAL,
                error_code=exc.code,
                execution_ref="admin:candidate-bundle:v1",
            )
            try:
                self._repository.add_stage_execution(failed)
                self._repository.update_run(
                    current.transition(
                        IngestionRunState.FAILED_FINAL,
                        at=failed.completed_at,
                    )
                )
            except ValueError:
                pass
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_BUILD_INVALID",
                "Candidate bundle could not be built from the accepted Source Brief",
            ) from exc

        if tuple(draft.proposal_kind for draft in result.proposals) != _EXPECTED_KINDS:
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_BUILD_INVALID",
                "Candidate bundle stage emitted an invalid proposal set",
            )
        if any(
            draft.payload_schema_version != BUNDLE_SCHEMA_VERSION
            or draft.risk_code != BUNDLE_RISK_CODE
            for draft in result.proposals
        ):
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_BUILD_INVALID",
                "Candidate bundle stage output contract is invalid",
            )

        completed_at = self._clock()
        execution = StageExecution(
            id=stage_id,
            run_id=current.id,
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
            attempt_no=1,
            max_attempts=1,
            executor_kind=ExecutorKind.DETERMINISTIC,
            input_hash=current.input_content_hash,
            output_hash=result.output_hash,
            started_at=started_at,
            completed_at=completed_at,
            outcome=StageOutcome.SUCCEEDED,
            execution_ref="admin:candidate-bundle:v1",
        )
        proposals = tuple(
            Proposal(
                id=proposal_id,
                proposal_kind=draft.proposal_kind,
                payload_schema_ref=draft.payload_schema_ref,
                payload_schema_version=draft.payload_schema_version,
                payload=draft.payload,
                payload_hash=stable_payload_hash(draft.payload),
                run_id=current.id,
                stage_execution_id=execution.id,
                created_at=completed_at,
                taxonomy_version=draft.taxonomy_version,
                configuration_version=draft.configuration_version,
                methodology_version=draft.methodology_version,
                confidence=draft.confidence,
                risk_code=draft.risk_code,
                ai_execution_ref=draft.ai_execution_ref,
                provenance_ref=draft.provenance_ref,
                supersedes_proposal_id=draft.supersedes_proposal_id,
            )
            for proposal_id, draft in zip(
                proposal_ids,
                result.proposals,
                strict=True,
            )
        )
        try:
            self._repository.complete_successful_stage(execution, proposals)
        except ValueError as exc:
            recovered = self._recover(
                run=current,
                stage_id=stage_id,
                proposal_ids=proposal_ids,
            )
            if recovered is not None:
                return recovered
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle atomic stage batch could not be recovered",
            ) from exc
        completed = self._ingestion.mark_succeeded(current.id)
        return completed, (proposals[0], proposals[1], proposals[2])

    def _recover(
        self,
        *,
        run: IngestionRun,
        stage_id: UUID,
        proposal_ids: tuple[UUID, UUID, UUID],
    ) -> tuple[IngestionRun, tuple[Proposal, Proposal, Proposal]] | None:
        current = self._repository.get_run(run.id)
        if current is None:
            return None
        history = self._repository.list_stage_executions(
            run.id,
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
        )
        proposals = tuple(
            self._repository.get_proposal(proposal_id)
            for proposal_id in proposal_ids
        )
        if not history and all(proposal is None for proposal in proposals):
            return None
        if len(history) != 1 or any(proposal is None for proposal in proposals):
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle ingestion history is incomplete",
            )
        execution = history[0]
        concrete = tuple(proposal for proposal in proposals if proposal is not None)
        if (
            execution.id != stage_id
            or execution.outcome is not StageOutcome.SUCCEEDED
            or execution.input_hash != run.input_content_hash
            or tuple(proposal.proposal_kind for proposal in concrete) != _EXPECTED_KINDS
            or any(
                proposal.run_id != run.id
                or proposal.stage_execution_id != stage_id
                or proposal.risk_code != BUNDLE_RISK_CODE
                for proposal in concrete
            )
        ):
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle ingestion history is inconsistent",
            )
        if current.state is IngestionRunState.RUNNING:
            current = self._ingestion.mark_succeeded(current.id)
        if current.state is not IngestionRunState.SUCCEEDED:
            raise _error(
                "ADMIN_CANDIDATE_BUNDLE_RUN_INVALID",
                "Candidate bundle ingestion run is not successful",
            )
        return current, (concrete[0], concrete[1], concrete[2])


__all__ = [
    "CandidateBundleResult",
    "SecuredCandidateBundleService",
]

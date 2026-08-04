from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid5

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.feed_item_review import (
    FeedItemReviewRecord,
    SecuredFeedItemReviewService,
)
from kefe_api.modules.admin_security.models import AdminPrincipal
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
    ProposalTargetMaterializer,
)
from kefe_api.modules.ingestion_orchestration.service import (
    FinalStageError,
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.source_brief_ingestion import (
    CONFIGURATION_HASH,
    NORMALIZED_SCHEMA_VERSION,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    SOURCE_BRIEF_KIND,
    SOURCE_BRIEF_RISK_CODE,
    SOURCE_BRIEF_SCHEMA_REF,
    SOURCE_BRIEF_SCHEMA_VERSION,
    STAGE_CODE,
    STAGE_VERSION,
    NormalizedFeedItemMetadata,
    SourceBriefStageProcessor,
    canonical_normalized_content_hash,
    require_source_brief_normalized_artifact,
)
from kefe_api.modules.knowledge.models import ArtifactKind, NormalizedArtifact
from kefe_api.modules.knowledge.ports import KnowledgeRepository

_NORMALIZED_NAMESPACE = UUID("877f43d2-1aa0-467e-b9af-1fbc3f146ec4")
_STAGE_NAMESPACE = UUID("af19e48e-81ce-481e-bd62-cf2f1c7e29a5")
_PROPOSAL_NAMESPACE = UUID("ecf32630-2b19-4f34-b30b-6ef8fc9e5f85")
_TARGET_KIND = "NORMALIZED_ARTIFACT"


def _domain_error(code: str, message: str, status: int = 409) -> DomainError:
    return DomainError(code, message, status)


class AcceptedFeedItemNormalizer(ProposalTargetMaterializer):
    def __init__(
        self,
        *,
        record: FeedItemReviewRecord,
        knowledge: KnowledgeRepository,
    ) -> None:
        self._record = record
        self._knowledge = knowledge

    def materialize(
        self,
        *,
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> tuple[str, UUID]:
        expected = self._record.queue_record
        if proposal != expected.proposal or review != expected.review:
            raise ValueError("feed item normalization input drifted")
        if review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise ValueError("feed item must be accepted before normalization")

        payload = self._record.payload
        source = self._knowledge.get_source_artifact(payload.source_artifact_id)
        if source is None:
            raise ValueError("feed item source artifact is missing")
        if (
            source.content_hash != payload.feed_content_hash
            or source.raw_storage_ref != payload.feed_storage_ref
        ):
            raise ValueError("feed item source artifact drifted")

        metadata = NormalizedFeedItemMetadata(
            parent_feed_item_proposal_id=proposal.id,
            review_decision_id=review.id,
            source_artifact_id=source.id,
            feed_content_hash=payload.feed_content_hash,
            feed_storage_ref=payload.feed_storage_ref,
            feed_format=payload.feed_format,
            feed_title=payload.feed_title,
            publisher_or_issuer=source.publisher_or_issuer,
            item_id=payload.item_id,
            item_title=payload.item_title,
            item_url=payload.item_url,
            published_at=payload.published_at,
            summary_text=payload.summary_text,
        )
        mapping = metadata.as_mapping()
        artifact_id = uuid5(
            _NORMALIZED_NAMESPACE,
            f"{proposal.id}:{review.id}:{NORMALIZED_SCHEMA_VERSION}",
        )
        artifact = NormalizedArtifact(
            id=artifact_id,
            source_artifact_id=source.id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=review.decided_at,
            content_hash=canonical_normalized_content_hash(mapping),
            text=payload.summary_text or payload.item_title,
            language_code=source.language_code,
            jurisdiction_code=(
                source.jurisdiction_code or expected.run.jurisdiction_code
            ),
            media_metadata=mapping,
        )
        existing = self._knowledge.get_normalized_artifact(artifact_id)
        if existing is not None:
            if existing != artifact:
                raise ValueError("normalized feed item identity collision")
            return _TARGET_KIND, artifact_id
        self._knowledge.add_normalized_artifact(artifact)
        return _TARGET_KIND, artifact_id


class SourceBriefIngestionResult:
    __slots__ = (
        "normalized_artifact_id",
        "run_id",
        "source_brief_proposal_id",
        "run_state",
    )

    def __init__(
        self,
        *,
        normalized_artifact_id: UUID,
        run_id: UUID,
        source_brief_proposal_id: UUID,
        run_state: IngestionRunState,
    ) -> None:
        self.normalized_artifact_id = normalized_artifact_id
        self.run_id = run_id
        self.source_brief_proposal_id = source_brief_proposal_id
        self.run_state = run_state


class SecuredSourceBriefIngestionService:
    def __init__(
        self,
        *,
        feed_items: SecuredFeedItemReviewService,
        ingestion: IngestionOrchestrationService,
        repository: IngestionOrchestrationRepository,
        knowledge: KnowledgeRepository,
        processor: SourceBriefStageProcessor,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._feed_items = feed_items
        self._ingestion = ingestion
        self._repository = repository
        self._knowledge = knowledge
        self._processor = processor
        self._clock = clock

    def build(
        self,
        principal: AdminPrincipal,
        proposal_id: UUID,
    ) -> SourceBriefIngestionResult:
        record = self._feed_items.detail(principal, proposal_id)
        review = record.queue_record.review
        if review is None or review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_REVIEW_REQUIRED",
                "Feed item must have an ACCEPTED review decision",
            )

        try:
            materialization = self._ingestion.materialize_accepted_proposal(
                proposal_id=proposal_id,
                materializer=AcceptedFeedItemNormalizer(
                    record=record,
                    knowledge=self._knowledge,
                ),
            )
        except (KeyError, ValueError) as exc:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_NORMALIZATION_INVALID",
                "Accepted feed item could not be normalized",
            ) from exc
        if materialization.target_kind != _TARGET_KIND:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_NORMALIZATION_INVALID",
                "Accepted feed item normalization target is invalid",
            )

        artifact = self._knowledge.get_normalized_artifact(materialization.target_id)
        if artifact is None:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_NORMALIZATION_INVALID",
                "Normalized feed item artifact is missing",
            )
        try:
            metadata = require_source_brief_normalized_artifact(artifact)
        except FinalStageError as exc:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_NORMALIZATION_INVALID",
                "Normalized feed item artifact is invalid",
            ) from exc
        if (
            metadata.parent_feed_item_proposal_id != proposal_id
            or metadata.review_decision_id != review.id
        ):
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_NORMALIZATION_INVALID",
                "Normalized feed item lineage is invalid",
            )

        run = self._ingestion.start_run(
            input_artifact_kind=InputArtifactKind.NORMALIZED_ARTIFACT,
            input_artifact_id=artifact.id,
            input_content_hash=artifact.content_hash,
            pipeline_code=PIPELINE_CODE,
            pipeline_version=PIPELINE_VERSION,
            configuration_hash=CONFIGURATION_HASH,
            locale=artifact.language_code or record.queue_record.run.locale,
            jurisdiction_code=(
                artifact.jurisdiction_code or record.queue_record.run.jurisdiction_code
            ),
        )
        completed, proposal = self._execute(run)
        return SourceBriefIngestionResult(
            normalized_artifact_id=artifact.id,
            run_id=completed.id,
            source_brief_proposal_id=proposal.id,
            run_state=completed.state,
        )

    def _execute(self, run: IngestionRun) -> tuple[IngestionRun, Proposal]:
        expected_stage_id = uuid5(
            _STAGE_NAMESPACE,
            f"{run.id}:{STAGE_CODE}:{STAGE_VERSION}:1",
        )
        expected_proposal_id = uuid5(
            _PROPOSAL_NAMESPACE,
            f"{run.id}:{SOURCE_BRIEF_KIND}:{SOURCE_BRIEF_SCHEMA_VERSION}",
        )
        recovered = self._recover(
            run=run,
            stage_id=expected_stage_id,
            proposal_id=expected_proposal_id,
        )
        if recovered is not None:
            return recovered

        current = self._repository.get_run(run.id)
        if current is None:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief ingestion run is missing",
            )
        if current.state is IngestionRunState.QUEUED:
            current = current.transition(IngestionRunState.RUNNING, at=self._clock())
            self._repository.update_run(current)
        elif current.state is not IngestionRunState.RUNNING:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief ingestion run is not executable",
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
                id=expected_stage_id,
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
                execution_ref="admin:source-brief:v1",
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
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_BUILD_INVALID",
                "Source Brief could not be built from normalized feed item",
            ) from exc

        if len(result.proposals) != 1:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_BUILD_INVALID",
                "Source Brief stage emitted an invalid proposal count",
            )
        draft = result.proposals[0]
        if (
            draft.proposal_kind != SOURCE_BRIEF_KIND
            or draft.payload_schema_ref != SOURCE_BRIEF_SCHEMA_REF
            or draft.payload_schema_version != SOURCE_BRIEF_SCHEMA_VERSION
            or draft.risk_code != SOURCE_BRIEF_RISK_CODE
        ):
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_BUILD_INVALID",
                "Source Brief stage output contract is invalid",
            )

        completed_at = self._clock()
        execution = StageExecution(
            id=expected_stage_id,
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
            execution_ref="admin:source-brief:v1",
        )
        proposal = Proposal(
            id=expected_proposal_id,
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
        try:
            self._repository.complete_successful_stage(execution, (proposal,))
        except ValueError as exc:
            recovered = self._recover(
                run=current,
                stage_id=expected_stage_id,
                proposal_id=expected_proposal_id,
            )
            if recovered is not None:
                return recovered
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief atomic stage batch could not be recovered",
            ) from exc
        completed = self._ingestion.mark_succeeded(current.id)
        return completed, proposal

    def _recover(
        self,
        *,
        run: IngestionRun,
        stage_id: UUID,
        proposal_id: UUID,
    ) -> tuple[IngestionRun, Proposal] | None:
        current = self._repository.get_run(run.id)
        if current is None:
            return None
        history = self._repository.list_stage_executions(
            run.id,
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
        )
        proposal = self._repository.get_proposal(proposal_id)
        if not history and proposal is None:
            return None
        if len(history) != 1 or proposal is None:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief ingestion history is inconsistent",
            )
        execution = history[0]
        if (
            execution.id != stage_id
            or execution.outcome is not StageOutcome.SUCCEEDED
            or execution.input_hash != run.input_content_hash
            or proposal.run_id != run.id
            or proposal.stage_execution_id != stage_id
            or proposal.proposal_kind != SOURCE_BRIEF_KIND
            or proposal.payload_schema_ref != SOURCE_BRIEF_SCHEMA_REF
            or proposal.payload_schema_version != SOURCE_BRIEF_SCHEMA_VERSION
        ):
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief ingestion history is inconsistent",
            )
        if current.state is IngestionRunState.RUNNING:
            current = self._ingestion.mark_succeeded(current.id)
        if current.state is not IngestionRunState.SUCCEEDED:
            raise _domain_error(
                "ADMIN_SOURCE_BRIEF_RUN_INVALID",
                "Source Brief ingestion run is not successful",
            )
        return current, proposal


__all__ = [
    "AcceptedFeedItemNormalizer",
    "SecuredSourceBriefIngestionService",
    "SourceBriefIngestionResult",
]

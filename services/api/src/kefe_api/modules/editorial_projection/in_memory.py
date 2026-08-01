from __future__ import annotations

from threading import RLock
from uuid import UUID

from kefe_api.modules.content_authoring.in_memory import (
    InMemoryContentAuthoringRepository,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    LifecycleAuditEntry,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionProfile,
    EditorialProjectionRecord,
    ReviewedProposalBundle,
)


class InMemoryReviewedProposalSource:
    def __init__(self, bundles: tuple[ReviewedProposalBundle, ...] = ()) -> None:
        self._bundles = {
            (bundle.candidate.id, bundle.candidate.review_decision_id): bundle
            for bundle in bundles
        }

    def add(self, bundle: ReviewedProposalBundle) -> None:
        self._bundles[(bundle.candidate.id, bundle.candidate.review_decision_id)] = bundle

    def get_bundle(
        self,
        candidate_proposal_id: UUID,
        proposal_review_decision_id: UUID,
    ) -> ReviewedProposalBundle | None:
        return self._bundles.get(
            (candidate_proposal_id, proposal_review_decision_id)
        )


class InMemoryEditorialProjectionProfileRegistry:
    def __init__(self, profiles: tuple[EditorialProjectionProfile, ...] = ()) -> None:
        self._profiles = {
            (profile.profile_code, profile.profile_version): profile
            for profile in profiles
        }

    def get(
        self,
        profile_code: str,
        profile_version: int,
    ) -> EditorialProjectionProfile | None:
        return self._profiles.get((profile_code, profile_version))


class InMemoryEditorialProjectionRepository:
    def __init__(
        self,
        authoring_repository: InMemoryContentAuthoringRepository | None = None,
    ) -> None:
        self.authoring_repository = (
            authoring_repository or InMemoryContentAuthoringRepository()
        )
        self._records_by_idempotency: dict[
            tuple[UUID, str], EditorialProjectionRecord
        ] = {}
        self._records_by_candidate: dict[UUID, EditorialProjectionRecord] = {}
        self._lock = RLock()

    def get_by_idempotency(
        self,
        candidate_proposal_id: UUID,
        idempotency_key: str,
    ) -> EditorialProjectionRecord | None:
        with self._lock:
            return self._records_by_idempotency.get(
                (candidate_proposal_id, idempotency_key)
            )

    def get_by_candidate(
        self,
        candidate_proposal_id: UUID,
    ) -> EditorialProjectionRecord | None:
        with self._lock:
            return self._records_by_candidate.get(candidate_proposal_id)

    def create_atomically(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
        record: EditorialProjectionRecord,
    ) -> None:
        with self._lock:
            key = (record.candidate_proposal_id, record.idempotency_key)
            if key in self._records_by_idempotency:
                raise ValueError("projection idempotency key already exists")
            if record.candidate_proposal_id in self._records_by_candidate:
                raise ValueError("candidate proposal already projected")
            self.authoring_repository.create_case(
                identity=identity,
                initial_version=initial_version,
                audit=audit,
            )
            self._records_by_idempotency[key] = record
            self._records_by_candidate[record.candidate_proposal_id] = record

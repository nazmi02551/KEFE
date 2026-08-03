from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    ProposalDraft,
    StageProcessorResult,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


@dataclass
class StaticProcessor:
    draft: ProposalDraft

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self.draft,))


def test_postgres_admin_feed_item_materialization_http_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    try:
        source_hash = canonical_content_hash(f"admin-http:{uuid4()}".encode())
        source = app.state.knowledge_repository.add_source_artifact(
            SourceArtifact.create(
                adapter_code="test.pg_admin_feed_item.v1",
                external_locator=f"https://feeds.example.test/{uuid4()}.xml",
                captured_at=datetime.now(UTC),
                content_hash=source_hash,
                publisher_or_issuer="PostgreSQL Admin Feed",
                language_code="en",
                jurisdiction_code="ZZ",
                raw_storage_ref=canonical_storage_ref(source_hash),
            )
        )
        service = app.state.ingestion_orchestration_service
        repository = app.state.ingestion_orchestration_repository
        run = service.start_run(
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=source.id,
            input_content_hash=source.content_hash,
            pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
            pipeline_version="1.0.0",
            configuration_hash=f"sha256:{uuid4().hex}{uuid4().hex}",
            locale="en",
            jurisdiction_code="ZZ",
        )
        service.execute_stage(
            run_id=run.id,
            stage_code="EXTRACT_FEED_ITEMS",
            stage_version="1.0.0",
            input_hash=source.content_hash,
            max_attempts=1,
            executor_kind=ExecutorKind.DETERMINISTIC,
            processor=StaticProcessor(
                ProposalDraft(
                    proposal_kind="FEED_ITEM",
                    payload_schema_ref="kefe.feed-item",
                    payload_schema_version="1.0.0",
                    payload={
                        "source_artifact_id": str(source.id),
                        "feed_content_hash": source.content_hash,
                        "feed_storage_ref": source.raw_storage_ref,
                        "feed_format": "ATOM_1_0",
                        "feed_title": "PostgreSQL Admin Feed",
                        "item_id": f"urn:uuid:{uuid4()}",
                        "item_title": "PostgreSQL Admin HTTP item",
                        "item_url": "https://www.example.test/pg-admin/item",
                        "published_at": "2026-08-03T10:00:00+00:00",
                        "summary_text": "Explicit source verification command.",
                    },
                    provenance_ref=source.raw_storage_ref,
                )
            ),
        )
        proposal = repository.list_proposals(run.id)[0]

        reviewer_id = uuid4()
        app.state.admin_session_store.upsert_subject(
            reviewer_id,
            roles=frozenset({AdminRole.REVIEWER}),
        )
        now = datetime.now(UTC)
        issued = app.state.admin_session_store.issue(
            admin_subject_id=reviewer_id,
            authenticated_at=now,
            mfa_satisfied_at=now,
            expires_at=now + timedelta(hours=1),
        )
        client = TestClient(app)
        client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
        review_response = client.post(
            f"/internal/admin/v1/proposals/{proposal.id}/review",
            headers={ADMIN_CSRF_HEADER: issued.csrf_token},
            json={
                "decision": "ACCEPTED",
                "rationale": "PostgreSQL source verification review.",
                "policy_version": "feed-item-review-v1",
            },
        )
        assert review_response.status_code == 201
        review_id = UUID(
            review_response.json()["proposal_review_decision_id"]
        )
        path = (
            "/internal/admin/v1/feed-item-proposals/"
            f"{proposal.id}/materialization"
        )
        payload = {"proposal_review_decision_id": str(review_id)}
        assert repository.find_materialization(
            proposal.id,
            target_kind="NORMALIZED_ARTIFACT",
        ) is None

        first = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: issued.csrf_token},
            json=payload,
        )
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["replayed"] is False

        replay = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: issued.csrf_token},
            json=payload,
        )
        assert replay.status_code == 200
        replay_body = replay.json()
        assert replay_body["replayed"] is True
        assert replay_body["proposal_materialization_id"] == (
            first_body["proposal_materialization_id"]
        )
        materialization = repository.find_materialization(
            proposal.id,
            target_kind="NORMALIZED_ARTIFACT",
        )
        assert materialization is not None
        assert str(materialization.id) == first_body["proposal_materialization_id"]
        artifact = app.state.knowledge_repository.get_normalized_artifact(
            UUID(first_body["target_id"])
        )
        assert artifact is not None
        assert artifact.source_artifact_id == source.id
        assert artifact.media_metadata["review_id"] == str(review_id)
        assert source.raw_storage_ref not in repr(artifact.media_metadata)
    finally:
        get_settings.cache_clear()

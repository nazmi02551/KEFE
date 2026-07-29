from __future__ import annotations

from alembic import op

revision = "20260729_0015"
down_revision = "20260729_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS knowledge")
    op.execute(
        """
        CREATE TABLE knowledge.source_artifact (
            id uuid PRIMARY KEY,
            adapter_code text NOT NULL,
            external_locator text NOT NULL,
            captured_at timestamptz NOT NULL,
            content_hash text NOT NULL,
            external_id text,
            canonical_url text,
            publisher_or_issuer text,
            published_at timestamptz,
            language_code text,
            jurisdiction_code text,
            raw_storage_ref text,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(adapter_code, external_locator, content_hash)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.normalized_artifact (
            id uuid PRIMARY KEY,
            source_artifact_id uuid NOT NULL
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            artifact_kind text NOT NULL CHECK (
                artifact_kind IN ('ORIGINAL_CONTENT','REPLY','EXTERNAL_EVIDENCE','MEDIA','OTHER')
            ),
            normalized_at timestamptz NOT NULL,
            content_hash text NOT NULL,
            text_content text,
            language_code text,
            jurisdiction_code text,
            parent_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            reply_to_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            media_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (id <> parent_artifact_id),
            CHECK (id <> reply_to_artifact_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX normalized_artifact_source_idx
        ON knowledge.normalized_artifact(source_artifact_id, normalized_at)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.claim (
            id uuid PRIMARY KEY,
            normalized_text text NOT NULL CHECK (btrim(normalized_text) <> ''),
            language_code text NOT NULL CHECK (btrim(language_code) <> ''),
            created_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.claim_assessment (
            id uuid PRIMARY KEY,
            claim_id uuid NOT NULL REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            claim_type text NOT NULL CHECK (
                claim_type IN (
                    'FACTUAL','CAUSAL','BEHAVIORAL','MOTIVE',
                    'NORMATIVE','LEGAL','PROCESS','PREDICTION'
                )
            ),
            claim_state text NOT NULL CHECK (
                claim_state IN (
                    'VERIFIED','SUPPORTED','CLAIMED','DISPUTED',
                    'UNVERIFIED','UNRESOLVED','FALSE'
                )
            ),
            taxonomy_version text NOT NULL CHECK (btrim(taxonomy_version) <> ''),
            review_state text NOT NULL CHECK (review_state IN ('PROPOSED','ACCEPTED','REJECTED')),
            assessed_at timestamptz NOT NULL,
            methodology_version text,
            reviewer_ref text,
            rationale_code text,
            provenance_ref text,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX claim_assessment_history_idx
        ON knowledge.claim_assessment(claim_id, assessed_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.claim_assertion (
            id uuid PRIMARY KEY,
            claim_id uuid NOT NULL REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            claimant_kind text NOT NULL CHECK (btrim(claimant_kind) <> ''),
            claimant_ref text NOT NULL CHECK (btrim(claimant_ref) <> ''),
            asserted_at timestamptz NOT NULL,
            source_artifact_id uuid
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            normalized_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            provenance_ref text,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX claim_assertion_claim_idx
        ON knowledge.claim_assertion(claim_id, asserted_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.evidence_link (
            id uuid PRIMARY KEY,
            claim_id uuid NOT NULL REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            source_artifact_id uuid
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            normalized_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            relation text NOT NULL CHECK (relation IN ('SUPPORTS','CONTRADICTS','CONTEXTUALIZES')),
            review_state text NOT NULL CHECK (review_state IN ('PROPOSED','ACCEPTED','REJECTED')),
            provenance_ref text,
            created_at timestamptz NOT NULL,
            CHECK (num_nonnulls(source_artifact_id, normalized_artifact_id) = 1)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX evidence_link_claim_idx
        ON knowledge.evidence_link(claim_id, created_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.claim_relation (
            id uuid PRIMARY KEY,
            from_claim_id uuid NOT NULL REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            to_claim_id uuid NOT NULL REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            relation_code text NOT NULL CHECK (btrim(relation_code) <> ''),
            taxonomy_version text NOT NULL CHECK (btrim(taxonomy_version) <> ''),
            review_state text NOT NULL CHECK (review_state IN ('PROPOSED','ACCEPTED','REJECTED')),
            provenance_ref text,
            created_at timestamptz NOT NULL,
            CHECK (from_claim_id <> to_claim_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX claim_relation_from_idx
        ON knowledge.claim_relation(from_claim_id, created_at, id)
        """
    )
    op.execute(
        """
        CREATE INDEX claim_relation_to_idx
        ON knowledge.claim_relation(to_claim_id, created_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.argument (
            id uuid PRIMARY KEY,
            body text NOT NULL CHECK (btrim(body) <> ''),
            language_code text NOT NULL CHECK (btrim(language_code) <> ''),
            review_state text NOT NULL CHECK (review_state IN ('PROPOSED','ACCEPTED','REJECTED')),
            normalized_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            source_artifact_id uuid
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            author_or_claimant_ref text,
            provenance_ref text,
            created_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.argument_relation (
            id uuid PRIMARY KEY,
            argument_id uuid NOT NULL REFERENCES knowledge.argument(id) ON DELETE RESTRICT,
            claim_target_id uuid REFERENCES knowledge.claim(id) ON DELETE RESTRICT,
            question_target_id uuid REFERENCES content.question(id) ON DELETE RESTRICT,
            argument_target_id uuid REFERENCES knowledge.argument(id) ON DELETE RESTRICT,
            relation text NOT NULL CHECK (
                relation IN ('SUPPORTS','OPPOSES','REBUTS','QUALIFIES','BRIDGES')
            ),
            taxonomy_version text NOT NULL CHECK (btrim(taxonomy_version) <> ''),
            review_state text NOT NULL CHECK (review_state IN ('PROPOSED','ACCEPTED','REJECTED')),
            provenance_ref text,
            created_at timestamptz NOT NULL,
            CHECK (num_nonnulls(claim_target_id, question_target_id, argument_target_id) = 1),
            CHECK (argument_id <> argument_target_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX argument_relation_argument_idx
        ON knowledge.argument_relation(argument_id, created_at, id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge.argument_relation")
    op.execute("DROP TABLE IF EXISTS knowledge.argument")
    op.execute("DROP TABLE IF EXISTS knowledge.claim_relation")
    op.execute("DROP TABLE IF EXISTS knowledge.evidence_link")
    op.execute("DROP TABLE IF EXISTS knowledge.claim_assertion")
    op.execute("DROP TABLE IF EXISTS knowledge.claim_assessment")
    op.execute("DROP TABLE IF EXISTS knowledge.claim")
    op.execute("DROP TABLE IF EXISTS knowledge.normalized_artifact")
    op.execute("DROP TABLE IF EXISTS knowledge.source_artifact")
    op.execute("DROP SCHEMA IF EXISTS knowledge")

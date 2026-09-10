"""Add signal.dispatch_target_registry table for multi-target signal dispatch.

CAP-057 Phase 2: DatabaseInstitutionTargetResolver requires a persistent
registry of institutional targets per signal. Each signal can have multiple
targets with independent lifecycle states.

Invariants:
- Each (signal_id, target_id) pair is unique.
- dispatch_status transitions are one-way monotonic (enforced by application layer).
- Targets link to signal.qualified_signal(signal_id) for FK integrity.
- official_contact_channel is encrypted at rest by the application layer;
  this migration stores the ciphertext opaquely.
"""
from __future__ import annotations

from alembic import op

revision = "20260910_0043"
down_revision = "20260910_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE signal.dispatch_target_registry (
            registry_id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            signal_id               uuid        NOT NULL
                REFERENCES signal.qualified_signal(signal_id) ON DELETE CASCADE,
            target_id               uuid        NOT NULL,
            target_name             text        NOT NULL CHECK (char_length(target_name) >= 2),
            target_type             text        NOT NULL
                CHECK (target_type IN (
                    'MUNICIPAL_GOVERNMENT',
                    'MINISTRY_DEPARTMENT',
                    'REGULATORY_BODY',
                    'PUBLIC_UTILITY',
                    'CORPORATE_ENTITY',
                    'CIVIC_OMBUDSMAN'
                )),
            jurisdiction_level      text        NOT NULL CHECK (char_length(jurisdiction_level) >= 3),
            official_contact_ref    text        NOT NULL,
            dispatch_status         text        NOT NULL DEFAULT 'PROPOSED_TARGET'
                CHECK (dispatch_status IN (
                    'PROPOSED_TARGET',
                    'VERIFIED_TARGET',
                    'DISPATCHED',
                    'ACKNOWLEDGED',
                    'ACTION_PLEDGED',
                    'DECLINED_JURISDICTION'
                )),
            response_due_days       integer     NOT NULL DEFAULT 30
                CHECK (response_due_days >= 0 AND response_due_days <= 365),
            proposed_by_actor_id    uuid,
            verified_by_actor_id    uuid,
            dispatched_at           timestamptz,
            acknowledged_at         timestamptz,
            created_at              timestamptz NOT NULL DEFAULT now(),
            updated_at              timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT signal_dispatch_target_unique UNIQUE (signal_id, target_id),
            CONSTRAINT signal_dispatch_lifecycle_consistent
                CHECK (
                    (dispatch_status = 'PROPOSED_TARGET' AND dispatched_at IS NULL)
                    OR (dispatch_status = 'VERIFIED_TARGET' AND dispatched_at IS NULL)
                    OR (dispatch_status IN ('DISPATCHED','ACKNOWLEDGED','ACTION_PLEDGED')
                        AND dispatched_at IS NOT NULL)
                    OR dispatch_status = 'DECLINED_JURISDICTION'
                )
        )
        """
    )

    op.execute(
        """
        CREATE INDEX signal_dispatch_target_signal_idx
        ON signal.dispatch_target_registry (signal_id, dispatch_status)
        """
    )

    op.execute(
        """
        CREATE INDEX signal_dispatch_target_status_idx
        ON signal.dispatch_target_registry (dispatch_status, created_at DESC)
        WHERE dispatch_status IN ('PROPOSED_TARGET', 'VERIFIED_TARGET', 'DISPATCHED')
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS signal.dispatch_target_registry")

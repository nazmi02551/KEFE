"""PostgreSQL implementation of InstitutionTargetResolver (CAP-057 Phase 2).

Resolves institutional dispatch targets from signal.dispatch_target_registry
for use by SignalTargetRegistryService.

This adapter is the production InstitutionTargetResolver — it replaces
NullInstitutionTargetResolver once the Admin target management surface is live.

Invariants:
- Only returns targets with dispatch_status != 'DECLINED_JURISDICTION'.
- Targets are ordered: PROPOSED_TARGET last, ACKNOWLEDGED/ACTION_PLEDGED first
  (most advanced lifecycle state first).
- official_contact_ref is stored as the raw value (application-level encryption
  must be applied before insert; not enforced here).
- Does not mutate any state — read-only resolver.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    SignalTargetItem,
    TargetType,
)


class PostgresSignalDispatchTargetResolver:
    """Read-only InstitutionTargetResolver backed by PostgreSQL.

    Injected into SignalTargetRegistryService at composition time.

    Usage:
        resolver = PostgresSignalDispatchTargetResolver(db_connection)
        service = SignalTargetRegistryService(resolver=resolver)
    """

    def __init__(self, connection) -> None:
        self._conn = connection

    def resolve_targets(
        self,
        *,
        signal_id: UUID,
        case_version_id: UUID,  # noqa: ARG002
        primary_domain_code: str,  # noqa: ARG002
    ) -> list[SignalTargetItem]:
        """Return dispatch targets for the signal from PostgreSQL.

        Targets are ordered by lifecycle advancement (most advanced first).
        Declined targets are excluded.
        """
        rows = self._conn.execute(
            text(
                """
                SELECT
                    target_id,
                    target_name,
                    target_type,
                    jurisdiction_level,
                    official_contact_ref,
                    dispatch_status,
                    response_due_days,
                    dispatched_at,
                    acknowledged_at
                FROM signal.dispatch_target_registry
                WHERE signal_id = :signal_id
                  AND dispatch_status != 'DECLINED_JURISDICTION'
                ORDER BY
                    CASE dispatch_status
                        WHEN 'ACTION_PLEDGED'   THEN 1
                        WHEN 'ACKNOWLEDGED'     THEN 2
                        WHEN 'DISPATCHED'       THEN 3
                        WHEN 'VERIFIED_TARGET'  THEN 4
                        WHEN 'PROPOSED_TARGET'  THEN 5
                    END,
                    created_at ASC
                """
            ),
            {"signal_id": str(signal_id)},
        ).fetchall()

        return [
            SignalTargetItem(
                target_id=UUID(str(row.target_id)),
                target_name=row.target_name,
                target_type=TargetType(row.target_type),
                jurisdiction_level=row.jurisdiction_level,
                official_contact_channel=row.official_contact_ref,
                dispatch_status=DispatchStatus(row.dispatch_status),
                response_due_days=row.response_due_days,
                dispatched_at=row.dispatched_at,
                acknowledged_at=row.acknowledged_at,
            )
            for row in rows
        ]


class PostgresSignalDispatchTargetWriter:
    """Write-side adapter for signal.dispatch_target_registry.

    Manages target lifecycle transitions and new target proposals.
    Called by the Admin signal target management router (CAP-057 Phase 2).

    All mutations are explicit single-row operations to enforce one-way
    monotonic lifecycle transitions.
    """

    def __init__(self, connection) -> None:
        self._conn = connection

    def propose_target(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
        target_name: str,
        target_type: TargetType,
        jurisdiction_level: str,
        official_contact_ref: str,
        response_due_days: int = 30,
        proposed_by_actor_id: UUID | None = None,
    ) -> None:
        """Insert a new PROPOSED_TARGET record.

        Raises IntegrityError if (signal_id, target_id) already exists.
        """
        self._conn.execute(
            text(
                """
                INSERT INTO signal.dispatch_target_registry (
                    signal_id, target_id, target_name, target_type,
                    jurisdiction_level, official_contact_ref,
                    dispatch_status, response_due_days, proposed_by_actor_id
                ) VALUES (
                    :signal_id, :target_id, :target_name, :target_type,
                    :jurisdiction_level, :official_contact_ref,
                    'PROPOSED_TARGET', :response_due_days, :proposed_by_actor_id
                )
                """
            ),
            {
                "signal_id": str(signal_id),
                "target_id": str(target_id),
                "target_name": target_name,
                "target_type": target_type.value,
                "jurisdiction_level": jurisdiction_level,
                "official_contact_ref": official_contact_ref,
                "response_due_days": response_due_days,
                "proposed_by_actor_id": str(proposed_by_actor_id) if proposed_by_actor_id else None,
            },
        )

    def advance_to_verified(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
        verified_by_actor_id: UUID,
    ) -> bool:
        """Transition PROPOSED_TARGET → VERIFIED_TARGET.

        Returns True if the row was updated, False if not found or wrong status.
        """
        result = self._conn.execute(
            text(
                """
                UPDATE signal.dispatch_target_registry
                SET dispatch_status = 'VERIFIED_TARGET',
                    verified_by_actor_id = :verified_by,
                    updated_at = now()
                WHERE signal_id = :signal_id
                  AND target_id = :target_id
                  AND dispatch_status = 'PROPOSED_TARGET'
                """
            ),
            {
                "signal_id": str(signal_id),
                "target_id": str(target_id),
                "verified_by": str(verified_by_actor_id),
            },
        )
        return result.rowcount == 1

    def advance_to_dispatched(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
    ) -> bool:
        """Transition VERIFIED_TARGET → DISPATCHED.

        Returns True if updated, False otherwise.
        """
        result = self._conn.execute(
            text(
                """
                UPDATE signal.dispatch_target_registry
                SET dispatch_status = 'DISPATCHED',
                    dispatched_at = now(),
                    updated_at = now()
                WHERE signal_id = :signal_id
                  AND target_id = :target_id
                  AND dispatch_status = 'VERIFIED_TARGET'
                """
            ),
            {"signal_id": str(signal_id), "target_id": str(target_id)},
        )
        return result.rowcount == 1

    def advance_to_acknowledged(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
    ) -> bool:
        """Transition DISPATCHED → ACKNOWLEDGED."""
        result = self._conn.execute(
            text(
                """
                UPDATE signal.dispatch_target_registry
                SET dispatch_status = 'ACKNOWLEDGED',
                    acknowledged_at = now(),
                    updated_at = now()
                WHERE signal_id = :signal_id
                  AND target_id = :target_id
                  AND dispatch_status = 'DISPATCHED'
                """
            ),
            {"signal_id": str(signal_id), "target_id": str(target_id)},
        )
        return result.rowcount == 1

    def advance_to_action_pledged(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
    ) -> bool:
        """Transition ACKNOWLEDGED → ACTION_PLEDGED."""
        result = self._conn.execute(
            text(
                """
                UPDATE signal.dispatch_target_registry
                SET dispatch_status = 'ACTION_PLEDGED',
                    updated_at = now()
                WHERE signal_id = :signal_id
                  AND target_id = :target_id
                  AND dispatch_status = 'ACKNOWLEDGED'
                """
            ),
            {"signal_id": str(signal_id), "target_id": str(target_id)},
        )
        return result.rowcount == 1

    def decline_jurisdiction(
        self,
        *,
        signal_id: UUID,
        target_id: UUID,
    ) -> bool:
        """Transition any non-terminal status → DECLINED_JURISDICTION."""
        result = self._conn.execute(
            text(
                """
                UPDATE signal.dispatch_target_registry
                SET dispatch_status = 'DECLINED_JURISDICTION',
                    updated_at = now()
                WHERE signal_id = :signal_id
                  AND target_id = :target_id
                  AND dispatch_status NOT IN ('ACTION_PLEDGED', 'DECLINED_JURISDICTION')
                """
            ),
            {"signal_id": str(signal_id), "target_id": str(target_id)},
        )
        return result.rowcount == 1
"""Signal Target Registry

Maps qualified signals to institutional targets and manages dispatch tracking.

Invariants:
- SignalTargetRegistryService is the only surface that maps signals to targets.
- Institutional targets are never hardcoded; they are resolved via the
  InstitutionTargetResolver port (configurable, swappable in tests).
- Only VERIFIED_TARGET or higher dispatch status allows dispatch recording.
- dispatch_status transitions are one-way monotonic (no rollback).
- Target resolution is domain-code-aware: GOVERNANCE → legislative/regulatory,
  ENVIRONMENT → environmental agencies, SOCIAL → social services, etc.
- Signal dispatch does not imply editorial acceptance or publication.
  A [PROVISIONAL] consensus_statement must not be forwarded to targets.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol, Sequence
from uuid import UUID


class TargetType(str, Enum):
    MUNICIPAL_GOVERNMENT = "MUNICIPAL_GOVERNMENT"
    MINISTRY_DEPARTMENT = "MINISTRY_DEPARTMENT"
    REGULATORY_BODY = "REGULATORY_BODY"
    PUBLIC_UTILITY = "PUBLIC_UTILITY"
    CORPORATE_ENTITY = "CORPORATE_ENTITY"
    CIVIC_OMBUDSMAN = "CIVIC_OMBUDSMAN"


class DispatchStatus(str, Enum):
    """One-way monotonic dispatch lifecycle.

    PROPOSED_TARGET  → admin proposes an institution as a target
    VERIFIED_TARGET  → target verified via authority pipeline
    DISPATCHED       → signal formally sent to target
    ACKNOWLEDGED     → target confirmed receipt
    ACTION_PLEDGED   → target committed to action
    DECLINED_JURISDICTION → target denied jurisdiction (terminal)
    """
    PROPOSED_TARGET = "PROPOSED_TARGET"
    VERIFIED_TARGET = "VERIFIED_TARGET"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACTION_PLEDGED = "ACTION_PLEDGED"
    DECLINED_JURISDICTION = "DECLINED_JURISDICTION"


# Dispatch transitions allowed by the domain invariant
_VALID_TRANSITIONS: dict[DispatchStatus, set[DispatchStatus]] = {
    DispatchStatus.PROPOSED_TARGET: {DispatchStatus.VERIFIED_TARGET, DispatchStatus.DECLINED_JURISDICTION},
    DispatchStatus.VERIFIED_TARGET: {DispatchStatus.DISPATCHED, DispatchStatus.DECLINED_JURISDICTION},
    DispatchStatus.DISPATCHED: {DispatchStatus.ACKNOWLEDGED, DispatchStatus.DECLINED_JURISDICTION},
    DispatchStatus.ACKNOWLEDGED: {DispatchStatus.ACTION_PLEDGED},
    DispatchStatus.ACTION_PLEDGED: set(),
    DispatchStatus.DECLINED_JURISDICTION: set(),
}


@dataclass(frozen=True)
class SignalTargetItem:
    target_id: UUID
    target_name: str
    target_type: TargetType
    jurisdiction_level: str
    official_contact_channel: str
    dispatch_status: DispatchStatus
    response_due_days: int
    dispatched_at: datetime | None = None
    acknowledged_at: datetime | None = None

    def can_transition_to(self, next_status: DispatchStatus) -> bool:
        return next_status in _VALID_TRANSITIONS.get(self.dispatch_status, set())


@dataclass(frozen=True)
class SignalTargetRegistryReport:
    signal_id: UUID
    case_version_id: UUID
    primary_domain_code: str
    primary_target_id: UUID | None
    targets: Sequence[SignalTargetItem]
    certified_at: datetime
    registry_proof_hash: str

    @property
    def dispatch_eligible_targets(self) -> list[SignalTargetItem]:
        """Return targets that are VERIFIED_TARGET (ready to dispatch)."""
        return [
            t for t in self.targets
            if t.dispatch_status == DispatchStatus.VERIFIED_TARGET
        ]

    @property
    def dispatched_targets(self) -> list[SignalTargetItem]:
        return [
            t for t in self.targets
            if t.dispatch_status in (
                DispatchStatus.DISPATCHED,
                DispatchStatus.ACKNOWLEDGED,
                DispatchStatus.ACTION_PLEDGED,
            )
        ]

    @property
    def is_fully_dispatched(self) -> bool:
        return (
            len(self.targets) > 0
            and all(
                t.dispatch_status in (
                    DispatchStatus.DISPATCHED,
                    DispatchStatus.ACKNOWLEDGED,
                    DispatchStatus.ACTION_PLEDGED,
                    DispatchStatus.DECLINED_JURISDICTION,
                )
                for t in self.targets
            )
        )


class InstitutionTargetResolver(Protocol):
    """Port: resolves institutional targets for a signal.

    Implementors supply a list of SignalTargetItem records for a given
    signal_id / case_version_id / primary_domain_code tuple.

    This port is injected at composition time. The default implementation
    is NullInstitutionTargetResolver (returns empty list — no auto-dispatch).

    Production implementations integrate with the Admin target management
    surface (CAP-057 Admin Signal Target Ops).
    """

    def resolve_targets(
        self,
        *,
        signal_id: UUID,
        case_version_id: UUID,
        primary_domain_code: str,
    ) -> list[SignalTargetItem]:
        """Return candidate institutional targets for this signal.

        Returning an empty list means the signal is not yet targeted.
        The caller (SignalTargetRegistryService) accepts an empty list
        as a valid outcome — it does NOT auto-assign targets.
        """
        ...


class NullInstitutionTargetResolver:
    """Default no-op resolver.

    Returns no targets so that the system does not auto-dispatch signals
    without explicit institutional targeting. This is the safe default
    until the Admin target management UI (CAP-057) is in production.
    """

    def resolve_targets(
        self,
        *,
        signal_id: UUID,
        case_version_id: UUID,
        primary_domain_code: str,
    ) -> list[SignalTargetItem]:
        return []


@dataclass
class StaticInstitutionTargetResolver:
    """Test / development resolver backed by an explicit list.

    Allows unit and integration tests to inject deterministic targets
    without database access. Targets are returned as-is.
    """

    targets: list[SignalTargetItem] = field(default_factory=list)

    def resolve_targets(
        self,
        *,
        signal_id: UUID,  # noqa: ARG002
        case_version_id: UUID,  # noqa: ARG002
        primary_domain_code: str,  # noqa: ARG002
    ) -> list[SignalTargetItem]:
        return list(self.targets)


class SignalDispatchError(Exception):
    """Raised when a dispatch lifecycle transition is invalid."""


class SignalTargetRegistryService:
    """Manages the formal mapping, jurisdictional verification,
    and dispatch tracking of civic signals to decision-making bodies.

    Usage:
        resolver = NullInstitutionTargetResolver()  # or injected production resolver
        service = SignalTargetRegistryService(resolver=resolver)
        report = service.evaluate(
            signal_id=uuid,
            case_version_id=uuid,
            primary_domain_code="GOVERNANCE",
        )

    The service never auto-selects or auto-dispatches targets.
    Target assignment and dispatch triggering are explicit Admin operations.
    """

    def __init__(
        self,
        resolver: InstitutionTargetResolver | None = None,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._resolver = resolver or NullInstitutionTargetResolver()
        self._clock = clock

    def evaluate(
        self,
        *,
        signal_id: UUID,
        case_version_id: UUID,
        primary_domain_code: str,
        certified_at: datetime | None = None,
    ) -> SignalTargetRegistryReport:
        """Build a SignalTargetRegistryReport for the given signal.

        If the resolver returns no targets, the report has an empty targets
        list and primary_target_id=None. This is a valid outcome — it means
        the signal is awaiting institutional targeting.

        Does NOT raise if no targets are available. Callers must check
        report.targets before initiating dispatch.
        """
        if certified_at is None:
            certified_at = self._clock()

        targets = self._resolver.resolve_targets(
            signal_id=signal_id,
            case_version_id=case_version_id,
            primary_domain_code=primary_domain_code,
        )

        primary_target_id: UUID | None = targets[0].target_id if targets else None

        payload = (
            f"{signal_id}:{case_version_id}:{primary_domain_code}:"
            f"{primary_target_id}:{len(targets)}:{certified_at.isoformat()}"
        )
        registry_proof_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return SignalTargetRegistryReport(
            signal_id=signal_id,
            case_version_id=case_version_id,
            primary_domain_code=primary_domain_code,
            primary_target_id=primary_target_id,
            targets=targets,
            certified_at=certified_at,
            registry_proof_hash=registry_proof_hash,
        )

    @staticmethod
    def validate_transition(
        item: SignalTargetItem,
        next_status: DispatchStatus,
    ) -> None:
        """Raise SignalDispatchError if the transition is not permitted.

        Use before recording a dispatch lifecycle event to enforce
        one-way monotonic dispatch status transitions.
        """
        if not item.can_transition_to(next_status):
            raise SignalDispatchError(
                f"Cannot transition target {item.target_id} "
                f"from {item.dispatch_status.value} to {next_status.value}"
            )

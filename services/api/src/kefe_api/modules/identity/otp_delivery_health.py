from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from typing import Protocol
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    OtpDeliveryOperationalResult,
    OtpDeliveryOutcome,
)

logger = logging.getLogger(__name__)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _require_actor_ref(value: str) -> None:
    if (
        not value.startswith("admin:")
        or len(value) > 128
        or value != value.strip()
        or any(ord(char) < 32 for char in value)
    ):
        raise ValueError("OTP alert acknowledgement actor_ref is invalid")


class OtpDeliveryHealthSignal(StrEnum):
    QUIET = "QUIET"
    NOMINAL = "NOMINAL"
    ATTENTION = "ATTENTION"
    CRITICAL = "CRITICAL"


class OtpDeliveryHealthReason(StrEnum):
    FAILURE_COUNT_ATTENTION = "FAILURE_COUNT_ATTENTION"
    FAILURE_COUNT_CRITICAL = "FAILURE_COUNT_CRITICAL"
    UNAVAILABLE_COUNT_ATTENTION = "UNAVAILABLE_COUNT_ATTENTION"
    UNAVAILABLE_COUNT_CRITICAL = "UNAVAILABLE_COUNT_CRITICAL"
    FAILURE_RATIO_ATTENTION = "FAILURE_RATIO_ATTENTION"
    FAILURE_RATIO_CRITICAL = "FAILURE_RATIO_CRITICAL"


@dataclass(frozen=True, slots=True)
class OtpDeliveryHealthEvent:
    id: UUID
    observed_at: datetime
    channel: OtpChannel
    outcome: OtpDeliveryOutcome
    attempts: int
    status_code: int | None
    error_code: str | None

    def __post_init__(self) -> None:
        _require_utc(self.observed_at, "observed_at")
        if not 1 <= self.attempts <= 3:
            raise ValueError("OTP delivery health attempts are outside the supported range")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("OTP delivery health status code is outside the HTTP range")
        if self.error_code is not None:
            if (
                not self.error_code
                or self.error_code != self.error_code.strip()
                or len(self.error_code) > 128
                or any(ord(char) < 32 for char in self.error_code)
            ):
                raise ValueError("OTP delivery health error code is invalid")
        if self.outcome is OtpDeliveryOutcome.ACCEPTED and self.error_code is not None:
            raise ValueError("accepted OTP delivery health event cannot have an error code")
        if self.outcome is not OtpDeliveryOutcome.ACCEPTED and self.error_code is None:
            raise ValueError("failed OTP delivery health event requires an error code")


@dataclass(frozen=True, slots=True)
class OtpDeliveryHealthFacts:
    as_of: datetime
    window_started_at: datetime
    total_count: int
    accepted_count: int
    unavailable_count: int
    rejected_count: int
    attempts_total: int
    email_count: int
    sms_count: int
    latest_observed_at: datetime | None
    latest_accepted_at: datetime | None

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        _require_utc(self.window_started_at, "window_started_at")
        if self.window_started_at > self.as_of:
            raise ValueError("OTP delivery health window cannot start after as_of")
        for value in (
            self.total_count,
            self.accepted_count,
            self.unavailable_count,
            self.rejected_count,
            self.attempts_total,
            self.email_count,
            self.sms_count,
        ):
            if value < 0:
                raise ValueError("OTP delivery health counts must be non-negative")
        if self.accepted_count + self.unavailable_count + self.rejected_count != self.total_count:
            raise ValueError("OTP delivery outcome counts must equal total_count")
        if self.email_count + self.sms_count != self.total_count:
            raise ValueError("OTP delivery channel counts must equal total_count")
        if self.attempts_total < self.total_count:
            raise ValueError("OTP delivery attempts_total cannot be below total_count")
        for value, name in (
            (self.latest_observed_at, "latest_observed_at"),
            (self.latest_accepted_at, "latest_accepted_at"),
        ):
            if value is not None:
                _require_utc(value, name)
                if value > self.as_of:
                    raise ValueError(f"{name} cannot be after as_of")


@dataclass(frozen=True, slots=True)
class OtpDeliveryHealthPolicy:
    window: timedelta = timedelta(minutes=15)
    retention: timedelta = timedelta(days=7)
    minimum_ratio_sample: int = 5
    failure_count_attention: int = 3
    failure_count_critical: int = 10
    unavailable_count_attention: int = 2
    unavailable_count_critical: int = 5
    failure_ratio_attention_bps: int = 2_000
    failure_ratio_critical_bps: int = 5_000

    def __post_init__(self) -> None:
        if self.window < timedelta(minutes=1) or self.window > timedelta(days=1):
            raise ValueError("OTP delivery health window is outside the supported range")
        if self.retention < self.window or self.retention > timedelta(days=30):
            raise ValueError("OTP delivery health retention is outside the supported range")
        if not 1 <= self.minimum_ratio_sample <= 100_000:
            raise ValueError("OTP delivery health minimum ratio sample is invalid")
        for attention, critical, name in (
            (
                self.failure_count_attention,
                self.failure_count_critical,
                "failure count",
            ),
            (
                self.unavailable_count_attention,
                self.unavailable_count_critical,
                "unavailable count",
            ),
            (
                self.failure_ratio_attention_bps,
                self.failure_ratio_critical_bps,
                "failure ratio",
            ),
        ):
            if attention < 1 or critical < attention:
                raise ValueError(f"OTP delivery health {name} thresholds are invalid")
        if self.failure_ratio_critical_bps > 10_000:
            raise ValueError("OTP delivery health failure ratio exceeds 100 percent")

    @classmethod
    def from_seconds(
        cls,
        *,
        window_seconds: int,
        retention_seconds: int,
        minimum_ratio_sample: int,
        failure_count_attention: int,
        failure_count_critical: int,
        unavailable_count_attention: int,
        unavailable_count_critical: int,
        failure_ratio_attention_bps: int,
        failure_ratio_critical_bps: int,
    ) -> OtpDeliveryHealthPolicy:
        return cls(
            window=timedelta(seconds=window_seconds),
            retention=timedelta(seconds=retention_seconds),
            minimum_ratio_sample=minimum_ratio_sample,
            failure_count_attention=failure_count_attention,
            failure_count_critical=failure_count_critical,
            unavailable_count_attention=unavailable_count_attention,
            unavailable_count_critical=unavailable_count_critical,
            failure_ratio_attention_bps=failure_ratio_attention_bps,
            failure_ratio_critical_bps=failure_ratio_critical_bps,
        )


@dataclass(frozen=True, slots=True)
class OtpDeliveryAlertPolicy:
    cooldown: timedelta = timedelta(minutes=30)
    retention: timedelta = timedelta(days=30)

    def __post_init__(self) -> None:
        if self.cooldown < timedelta(minutes=1) or self.cooldown > timedelta(days=1):
            raise ValueError("OTP delivery alert cooldown is outside the supported range")
        if self.retention < self.cooldown or self.retention > timedelta(days=90):
            raise ValueError("OTP delivery alert retention is outside the supported range")

    @classmethod
    def from_seconds(
        cls,
        *,
        cooldown_seconds: int,
        retention_seconds: int,
    ) -> OtpDeliveryAlertPolicy:
        return cls(
            cooldown=timedelta(seconds=cooldown_seconds),
            retention=timedelta(seconds=retention_seconds),
        )


@dataclass(frozen=True, slots=True)
class OtpDeliveryHealthSnapshot:
    as_of: datetime
    signal: OtpDeliveryHealthSignal
    reason_codes: tuple[str, ...]
    facts: OtpDeliveryHealthFacts
    failure_ratio_bps: int | None
    policy: OtpDeliveryHealthPolicy

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        if self.facts.as_of != self.as_of:
            raise ValueError("OTP delivery health facts must share snapshot as_of")
        if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("OTP delivery health reason_codes must be sorted and unique")
        if self.failure_ratio_bps is not None and not 0 <= self.failure_ratio_bps <= 10_000:
            raise ValueError("OTP delivery health failure ratio is invalid")


@dataclass(frozen=True, slots=True)
class OtpDeliveryAlertCandidate:
    id: UUID
    signal: OtpDeliveryHealthSignal
    reason_codes: tuple[str, ...]
    observed_at: datetime
    window_started_at: datetime
    total_count: int
    accepted_count: int
    unavailable_count: int
    rejected_count: int
    failure_ratio_bps: int | None
    created_at: datetime

    def __post_init__(self) -> None:
        if self.signal not in (
            OtpDeliveryHealthSignal.ATTENTION,
            OtpDeliveryHealthSignal.CRITICAL,
        ):
            raise ValueError("OTP delivery alert candidate requires a degraded signal")
        if not self.reason_codes or tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("OTP delivery alert reason_codes must be sorted and unique")
        for value, name in (
            (self.observed_at, "observed_at"),
            (self.window_started_at, "window_started_at"),
            (self.created_at, "created_at"),
        ):
            _require_utc(value, name)
        if self.window_started_at > self.observed_at or self.created_at < self.observed_at:
            raise ValueError("OTP delivery alert timestamps are inconsistent")
        for value in (
            self.total_count,
            self.accepted_count,
            self.unavailable_count,
            self.rejected_count,
        ):
            if value < 0:
                raise ValueError("OTP delivery alert counts must be non-negative")
        if self.accepted_count + self.unavailable_count + self.rejected_count != self.total_count:
            raise ValueError("OTP delivery alert outcome counts must equal total_count")
        if self.failure_ratio_bps is not None and not 0 <= self.failure_ratio_bps <= 10_000:
            raise ValueError("OTP delivery alert failure ratio is invalid")

    @classmethod
    def from_snapshot(cls, snapshot: OtpDeliveryHealthSnapshot) -> OtpDeliveryAlertCandidate:
        facts = snapshot.facts
        return cls(
            id=uuid4(),
            signal=snapshot.signal,
            reason_codes=snapshot.reason_codes,
            observed_at=snapshot.as_of,
            window_started_at=facts.window_started_at,
            total_count=facts.total_count,
            accepted_count=facts.accepted_count,
            unavailable_count=facts.unavailable_count,
            rejected_count=facts.rejected_count,
            failure_ratio_bps=snapshot.failure_ratio_bps,
            created_at=snapshot.as_of,
        )


@dataclass(frozen=True, slots=True)
class OtpDeliveryAlertAcknowledgement:
    candidate_id: UUID
    acknowledged_at: datetime
    actor_ref: str
    created_at: datetime

    def __post_init__(self) -> None:
        _require_utc(self.acknowledged_at, "acknowledged_at")
        _require_utc(self.created_at, "created_at")
        if self.created_at < self.acknowledged_at:
            raise ValueError("OTP alert acknowledgement created_at cannot precede acknowledgement")
        _require_actor_ref(self.actor_ref)


@dataclass(frozen=True, slots=True)
class OtpDeliveryAlertRecord:
    candidate: OtpDeliveryAlertCandidate
    acknowledgement: OtpDeliveryAlertAcknowledgement | None

    def __post_init__(self) -> None:
        if (
            self.acknowledgement is not None
            and self.acknowledgement.candidate_id != self.candidate.id
        ):
            raise ValueError("OTP alert acknowledgement belongs to another candidate")

    @property
    def acknowledged(self) -> bool:
        return self.acknowledgement is not None


class OtpDeliveryHealthRepository(Protocol):
    def append_and_prune(
        self,
        event: OtpDeliveryHealthEvent,
        *,
        prune_before: datetime,
    ) -> None: ...

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpDeliveryHealthFacts: ...

    def list_alert_candidates(
        self,
        *,
        acknowledged: bool | None,
        limit: int,
        offset: int,
        as_of: datetime,
    ) -> tuple[OtpDeliveryAlertRecord, ...]: ...

    def acknowledge_alert(
        self,
        acknowledgement: OtpDeliveryAlertAcknowledgement,
        *,
        as_of: datetime,
    ) -> OtpDeliveryAlertRecord | None: ...


class InMemoryOtpDeliveryHealthRepository:
    def __init__(
        self,
        *,
        health_policy: OtpDeliveryHealthPolicy | None = None,
        alert_policy: OtpDeliveryAlertPolicy | None = None,
    ) -> None:
        self._events: list[OtpDeliveryHealthEvent] = []
        self._alert_candidates: list[OtpDeliveryAlertCandidate] = []
        self._alert_acknowledgements: dict[UUID, OtpDeliveryAlertAcknowledgement] = {}
        self._health_policy = health_policy or OtpDeliveryHealthPolicy()
        self._alert_policy = alert_policy or OtpDeliveryAlertPolicy()
        self._lock = RLock()

    def append_and_prune(
        self,
        event: OtpDeliveryHealthEvent,
        *,
        prune_before: datetime,
    ) -> None:
        _require_utc(prune_before, "prune_before")
        with self._lock:
            self._events = [
                current for current in self._events if current.observed_at >= prune_before
            ]
            self._events.append(event)
            window_started_at = event.observed_at - self._health_policy.window
            events = [
                current
                for current in self._events
                if window_started_at <= current.observed_at <= event.observed_at
            ]
            facts = _facts_from_events(
                events,
                window_started_at=window_started_at,
                as_of=event.observed_at,
            )
            snapshot = _snapshot_from_facts(facts, self._health_policy)
            self._prune_alerts_locked(event.observed_at - self._alert_policy.retention)
            self._append_alert_candidate_if_due_locked(snapshot)

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpDeliveryHealthFacts:
        _require_utc(window_started_at, "window_started_at")
        _require_utc(as_of, "as_of")
        _require_utc(prune_before, "prune_before")
        with self._lock:
            self._events = [
                event for event in self._events if event.observed_at >= prune_before
            ]
            events = [
                event
                for event in self._events
                if window_started_at <= event.observed_at <= as_of
            ]
        return _facts_from_events(events, window_started_at=window_started_at, as_of=as_of)

    def list_alert_candidates(
        self,
        *,
        acknowledged: bool | None,
        limit: int,
        offset: int,
        as_of: datetime,
    ) -> tuple[OtpDeliveryAlertRecord, ...]:
        _validate_alert_page(limit=limit, offset=offset)
        _require_utc(as_of, "as_of")
        with self._lock:
            self._prune_alerts_locked(as_of - self._alert_policy.retention)
            candidates = sorted(
                self._alert_candidates,
                key=lambda item: (item.observed_at, str(item.id)),
                reverse=True,
            )
            records = [self._record_locked(candidate) for candidate in candidates]
            if acknowledged is not None:
                records = [record for record in records if record.acknowledged is acknowledged]
            return tuple(records[offset : offset + limit])

    def acknowledge_alert(
        self,
        acknowledgement: OtpDeliveryAlertAcknowledgement,
        *,
        as_of: datetime,
    ) -> OtpDeliveryAlertRecord | None:
        _require_utc(as_of, "as_of")
        with self._lock:
            self._prune_alerts_locked(as_of - self._alert_policy.retention)
            candidate = next(
                (
                    item
                    for item in self._alert_candidates
                    if item.id == acknowledgement.candidate_id
                ),
                None,
            )
            if candidate is None:
                return None
            self._alert_acknowledgements.setdefault(candidate.id, acknowledgement)
            return self._record_locked(candidate)

    def _append_alert_candidate_if_due_locked(
        self,
        snapshot: OtpDeliveryHealthSnapshot,
    ) -> None:
        if snapshot.signal not in (
            OtpDeliveryHealthSignal.ATTENTION,
            OtpDeliveryHealthSignal.CRITICAL,
        ):
            return
        cooldown_started_at = snapshot.as_of - self._alert_policy.cooldown
        current_rank = _signal_rank(snapshot.signal)
        if any(
            candidate.observed_at >= cooldown_started_at
            and _signal_rank(candidate.signal) >= current_rank
            for candidate in self._alert_candidates
        ):
            return
        self._alert_candidates.append(OtpDeliveryAlertCandidate.from_snapshot(snapshot))

    def _prune_alerts_locked(self, prune_before: datetime) -> None:
        retained = [
            candidate
            for candidate in self._alert_candidates
            if candidate.observed_at >= prune_before
        ]
        retained_ids = {candidate.id for candidate in retained}
        self._alert_candidates = retained
        self._alert_acknowledgements = {
            candidate_id: acknowledgement
            for candidate_id, acknowledgement in self._alert_acknowledgements.items()
            if candidate_id in retained_ids
        }

    def _record_locked(self, candidate: OtpDeliveryAlertCandidate) -> OtpDeliveryAlertRecord:
        return OtpDeliveryAlertRecord(
            candidate=candidate,
            acknowledgement=self._alert_acknowledgements.get(candidate.id),
        )


class DurableOtpDeliveryObserver:
    def __init__(
        self,
        repository: OtpDeliveryHealthRepository,
        *,
        retention: timedelta,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        if retention < timedelta(minutes=1):
            raise ValueError("OTP delivery health retention must be positive")
        self._repository = repository
        self._retention = retention
        self._clock = clock

    def record(self, result: OtpDeliveryOperationalResult) -> None:
        observed_at = self._clock()
        _require_utc(observed_at, "observed_at")
        self._repository.append_and_prune(
            OtpDeliveryHealthEvent(
                id=uuid4(),
                observed_at=observed_at,
                channel=result.channel,
                outcome=result.outcome,
                attempts=result.attempts,
                status_code=result.status_code,
                error_code=result.error_code,
            ),
            prune_before=observed_at - self._retention,
        )


class FailOpenOtpDeliveryObserver:
    """Preserve provider semantics when best-effort health persistence fails."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate

    def record(self, result: OtpDeliveryOperationalResult) -> None:
        try:
            self._delegate.record(result)
        except Exception:  # noqa: BLE001 - telemetry must not alter delivery semantics
            logger.exception("OTP delivery health observation failed")


class OtpDeliveryHealthService:
    def __init__(self, repository: OtpDeliveryHealthRepository) -> None:
        self._repository = repository

    def snapshot(
        self,
        policy: OtpDeliveryHealthPolicy | None = None,
        *,
        as_of: datetime | None = None,
    ) -> OtpDeliveryHealthSnapshot:
        resolved_policy = policy or OtpDeliveryHealthPolicy()
        resolved_as_of = as_of or datetime.now(UTC)
        _require_utc(resolved_as_of, "as_of")
        facts = self._repository.read_facts(
            window_started_at=resolved_as_of - resolved_policy.window,
            as_of=resolved_as_of,
            prune_before=resolved_as_of - resolved_policy.retention,
        )
        return _snapshot_from_facts(facts, resolved_policy)

    def list_alert_candidates(
        self,
        *,
        acknowledged: bool | None = None,
        limit: int = 50,
        offset: int = 0,
        as_of: datetime | None = None,
    ) -> tuple[OtpDeliveryAlertRecord, ...]:
        resolved_as_of = as_of or datetime.now(UTC)
        _require_utc(resolved_as_of, "as_of")
        return self._repository.list_alert_candidates(
            acknowledged=acknowledged,
            limit=limit,
            offset=offset,
            as_of=resolved_as_of,
        )

    def acknowledge_alert(
        self,
        *,
        candidate_id: UUID,
        actor_ref: str,
        as_of: datetime | None = None,
    ) -> OtpDeliveryAlertRecord:
        resolved_as_of = as_of or datetime.now(UTC)
        _require_utc(resolved_as_of, "as_of")
        acknowledgement = OtpDeliveryAlertAcknowledgement(
            candidate_id=candidate_id,
            acknowledged_at=resolved_as_of,
            actor_ref=actor_ref,
            created_at=resolved_as_of,
        )
        record = self._repository.acknowledge_alert(
            acknowledgement,
            as_of=resolved_as_of,
        )
        if record is None:
            raise DomainError(
                "ADMIN_OPERATIONAL_ALERT_NOT_FOUND",
                "OTP delivery alert candidate was not found",
                404,
            )
        return record


def _snapshot_from_facts(
    facts: OtpDeliveryHealthFacts,
    policy: OtpDeliveryHealthPolicy,
) -> OtpDeliveryHealthSnapshot:
    failure_count = facts.unavailable_count + facts.rejected_count
    failure_ratio_bps = (
        failure_count * 10_000 // facts.total_count
        if facts.total_count >= policy.minimum_ratio_sample
        else None
    )
    reasons = _reason_codes(
        facts=facts,
        failure_count=failure_count,
        failure_ratio_bps=failure_ratio_bps,
        policy=policy,
    )
    signal = _signal(facts=facts, reasons=reasons)
    return OtpDeliveryHealthSnapshot(
        as_of=facts.as_of,
        signal=signal,
        reason_codes=tuple(sorted(reasons)),
        facts=facts,
        failure_ratio_bps=failure_ratio_bps,
        policy=policy,
    )


def _reason_codes(
    *,
    facts: OtpDeliveryHealthFacts,
    failure_count: int,
    failure_ratio_bps: int | None,
    policy: OtpDeliveryHealthPolicy,
) -> set[str]:
    reasons: set[str] = set()
    if failure_count >= policy.failure_count_critical:
        reasons.add(OtpDeliveryHealthReason.FAILURE_COUNT_CRITICAL.value)
    elif failure_count >= policy.failure_count_attention:
        reasons.add(OtpDeliveryHealthReason.FAILURE_COUNT_ATTENTION.value)
    if facts.unavailable_count >= policy.unavailable_count_critical:
        reasons.add(OtpDeliveryHealthReason.UNAVAILABLE_COUNT_CRITICAL.value)
    elif facts.unavailable_count >= policy.unavailable_count_attention:
        reasons.add(OtpDeliveryHealthReason.UNAVAILABLE_COUNT_ATTENTION.value)
    if failure_ratio_bps is not None:
        if failure_ratio_bps >= policy.failure_ratio_critical_bps:
            reasons.add(OtpDeliveryHealthReason.FAILURE_RATIO_CRITICAL.value)
        elif failure_ratio_bps >= policy.failure_ratio_attention_bps:
            reasons.add(OtpDeliveryHealthReason.FAILURE_RATIO_ATTENTION.value)
    return reasons


def _signal(
    *,
    facts: OtpDeliveryHealthFacts,
    reasons: set[str],
) -> OtpDeliveryHealthSignal:
    if any(reason.endswith("_CRITICAL") for reason in reasons):
        return OtpDeliveryHealthSignal.CRITICAL
    if reasons:
        return OtpDeliveryHealthSignal.ATTENTION
    if facts.total_count == 0:
        return OtpDeliveryHealthSignal.QUIET
    return OtpDeliveryHealthSignal.NOMINAL


def _signal_rank(signal: OtpDeliveryHealthSignal) -> int:
    return {
        OtpDeliveryHealthSignal.QUIET: 0,
        OtpDeliveryHealthSignal.NOMINAL: 1,
        OtpDeliveryHealthSignal.ATTENTION: 2,
        OtpDeliveryHealthSignal.CRITICAL: 3,
    }[signal]


def _validate_alert_page(*, limit: int, offset: int) -> None:
    if not 1 <= limit <= 100:
        raise ValueError("OTP delivery alert limit is outside the supported range")
    if not 0 <= offset <= 10_000:
        raise ValueError("OTP delivery alert offset is outside the supported range")


def _facts_from_events(
    events: list[OtpDeliveryHealthEvent],
    *,
    window_started_at: datetime,
    as_of: datetime,
) -> OtpDeliveryHealthFacts:
    accepted = [event for event in events if event.outcome is OtpDeliveryOutcome.ACCEPTED]
    return OtpDeliveryHealthFacts(
        as_of=as_of,
        window_started_at=window_started_at,
        total_count=len(events),
        accepted_count=len(accepted),
        unavailable_count=sum(
            event.outcome is OtpDeliveryOutcome.UNAVAILABLE for event in events
        ),
        rejected_count=sum(
            event.outcome is OtpDeliveryOutcome.REJECTED for event in events
        ),
        attempts_total=sum(event.attempts for event in events),
        email_count=sum(event.channel is OtpChannel.EMAIL for event in events),
        sms_count=sum(event.channel is OtpChannel.SMS for event in events),
        latest_observed_at=max((event.observed_at for event in events), default=None),
        latest_accepted_at=max(
            (event.observed_at for event in accepted),
            default=None,
        ),
    )


__all__ = [
    "DurableOtpDeliveryObserver",
    "FailOpenOtpDeliveryObserver",
    "InMemoryOtpDeliveryHealthRepository",
    "OtpDeliveryAlertAcknowledgement",
    "OtpDeliveryAlertCandidate",
    "OtpDeliveryAlertPolicy",
    "OtpDeliveryAlertRecord",
    "OtpDeliveryHealthEvent",
    "OtpDeliveryHealthFacts",
    "OtpDeliveryHealthPolicy",
    "OtpDeliveryHealthReason",
    "OtpDeliveryHealthRepository",
    "OtpDeliveryHealthService",
    "OtpDeliveryHealthSignal",
    "OtpDeliveryHealthSnapshot",
    "_snapshot_from_facts",
]

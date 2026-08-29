from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from kefe_api.modules.analytics.models import (
    ActivationJourney,
    AnalyticsEvent,
    QualityJourney,
)
from kefe_api.modules.analytics.registry import AnalyticsRegistry
from kefe_api.modules.events.models import OutboxEvent

FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "response",
        "responses",
        "response_body",
        "private_reason",
        "reason_text",
        "reason_tags",
        "text",
        "tags",
        "personality",
        "ideology",
        "psychometric",
        "bias",
        "causal_inference",
    }
)

ALLOWED_CONTRIBUTION_CLASSES = frozenset(
    {"CORE_PRE_RESULT", "EXPOSED", "ADVOCACY_SUPPORT"}
)


class AnalyticsProjectionError(ValueError):
    """A source event violates the governed analytics projection contract."""


class ActivationJourneyProjectionError(ValueError):
    """Analytics events disagree on session-level activation provenance."""


class QualityJourneyProjectionError(ValueError):
    """Analytics events disagree on session-level quality provenance."""


class ActivationJourneyProjector:
    _STAGES = {
        ("activation.weigh_started", 1): (
            "started_at",
            "started_source_event_id",
        ),
        ("activation.weigh_committed", 1): (
            "committed_at",
            "committed_source_event_id",
        ),
        ("activation.result_revealed", 1): (
            "result_revealed_at",
            "result_revealed_source_event_id",
        ),
    }

    @classmethod
    def supports(cls, event: AnalyticsEvent) -> bool:
        return (event.analytics_name, event.analytics_version) in cls._STAGES

    def apply(
        self,
        current: ActivationJourney | None,
        event: AnalyticsEvent,
    ) -> ActivationJourney | None:
        stage = self._STAGES.get((event.analytics_name, event.analytics_version))
        if stage is None:
            return current

        if current is None:
            if event.case_version_id is None:
                raise ActivationJourneyProjectionError(
                    "activation event requires case_version_id"
                )
            current = ActivationJourney(
                session_id=event.session_id,
                actor_id=event.actor_id,
                case_version_id=event.case_version_id,
                started_at=None,
                started_source_event_id=None,
                committed_at=None,
                committed_source_event_id=None,
                result_revealed_at=None,
                result_revealed_source_event_id=None,
            )
        else:
            self._validate_provenance(current, event)

        actor_id = current.actor_id or event.actor_id
        occurred_field, source_field = stage
        selected_at, selected_source = self._earliest_observation(
            current_at=getattr(current, occurred_field),
            current_source_event_id=getattr(current, source_field),
            candidate_at=event.occurred_at,
            candidate_source_event_id=event.source_event_id,
        )
        return replace(
            current,
            actor_id=actor_id,
            **{
                occurred_field: selected_at,
                source_field: selected_source,
            },
        )

    def rebuild(self, events: Iterable[AnalyticsEvent]) -> ActivationJourney | None:
        journey: ActivationJourney | None = None
        ordered = sorted(
            events,
            key=lambda event: (
                event.occurred_at,
                str(event.source_event_id),
                event.analytics_name,
                event.analytics_version,
            ),
        )
        for event in ordered:
            journey = self.apply(journey, event)
        return journey

    @staticmethod
    def _validate_provenance(
        current: ActivationJourney,
        event: AnalyticsEvent,
    ) -> None:
        if event.session_id != current.session_id:
            raise ActivationJourneyProjectionError("activation session_id conflict")
        if (
            current.actor_id is not None
            and event.actor_id is not None
            and current.actor_id != event.actor_id
        ):
            raise ActivationJourneyProjectionError("activation actor_id conflict")
        if event.case_version_id is None:
            raise ActivationJourneyProjectionError(
                "activation event requires case_version_id"
            )
        if current.case_version_id != event.case_version_id:
            raise ActivationJourneyProjectionError(
                "activation case_version_id conflict"
            )

    @staticmethod
    def _earliest_observation(
        *,
        current_at: datetime | None,
        current_source_event_id: UUID | None,
        candidate_at: datetime,
        candidate_source_event_id: UUID,
    ) -> tuple[datetime, UUID]:
        if current_at is None or current_source_event_id is None:
            return candidate_at, candidate_source_event_id
        current_key = (current_at, str(current_source_event_id))
        candidate_key = (candidate_at, str(candidate_source_event_id))
        if candidate_key < current_key:
            return candidate_at, candidate_source_event_id
        return current_at, current_source_event_id


class QualityJourneyProjector:
    _STAGES = {
        ("activation.weigh_committed", 1): (
            "committed_at",
            "committed_source_event_id",
        ),
        ("quality.perspective_viewed", 1): (
            "perspective_viewed_at",
            "perspective_viewed_source_event_id",
        ),
        ("quality.exposure_recorded", 1): (
            "exposure_recorded_at",
            "exposure_recorded_source_event_id",
        ),
        ("quality.intervention_exposed", 1): (
            "intervention_exposed_at",
            "intervention_exposed_source_event_id",
        ),
        ("quality.decision_revised", 1): (
            "decision_revised_at",
            "decision_revised_source_event_id",
        ),
    }

    @classmethod
    def supports(cls, event: AnalyticsEvent) -> bool:
        return (event.analytics_name, event.analytics_version) in cls._STAGES

    def apply(
        self,
        current: QualityJourney | None,
        event: AnalyticsEvent,
    ) -> QualityJourney | None:
        stage = self._STAGES.get((event.analytics_name, event.analytics_version))
        if stage is None:
            return current

        if current is None:
            current = QualityJourney(
                session_id=event.session_id,
                case_version_id=event.case_version_id,
                committed_at=None,
                committed_source_event_id=None,
                perspective_viewed_at=None,
                perspective_viewed_source_event_id=None,
                exposure_recorded_at=None,
                exposure_recorded_source_event_id=None,
                intervention_exposed_at=None,
                intervention_exposed_source_event_id=None,
                decision_revised_at=None,
                decision_revised_source_event_id=None,
            )
        else:
            self._validate_provenance(current, event)

        occurred_field, source_field = stage
        selected_at, selected_source = ActivationJourneyProjector._earliest_observation(
            current_at=getattr(current, occurred_field),
            current_source_event_id=getattr(current, source_field),
            candidate_at=event.occurred_at,
            candidate_source_event_id=event.source_event_id,
        )
        return replace(
            current,
            case_version_id=current.case_version_id or event.case_version_id,
            **{
                occurred_field: selected_at,
                source_field: selected_source,
            },
        )

    def rebuild(self, events: Iterable[AnalyticsEvent]) -> QualityJourney | None:
        journey: QualityJourney | None = None
        ordered = sorted(
            events,
            key=lambda event: (
                event.occurred_at,
                str(event.source_event_id),
                event.analytics_name,
                event.analytics_version,
            ),
        )
        for event in ordered:
            journey = self.apply(journey, event)
        return journey

    @staticmethod
    def _validate_provenance(
        current: QualityJourney,
        event: AnalyticsEvent,
    ) -> None:
        if event.session_id != current.session_id:
            raise QualityJourneyProjectionError("quality session_id conflict")
        if (
            current.case_version_id is not None
            and event.case_version_id is not None
            and current.case_version_id != event.case_version_id
        ):
            raise QualityJourneyProjectionError("quality case_version_id conflict")


class AnalyticsEventProjector:
    def __init__(self, *, registry: AnalyticsRegistry, producer_version: str) -> None:
        if not producer_version.strip():
            raise ValueError("producer_version is required")
        self._registry = dict(registry)
        self._producer_version = producer_version

    def project(self, source: OutboxEvent) -> AnalyticsEvent | None:
        definition = self._registry.get((source.event_name, source.event_version))
        if definition is None:
            return None

        self._reject_forbidden(source.payload)
        actor_id = self._uuid_field(source.payload, "actor_id")
        case_version_id = self._uuid_field(source.payload, "case_version_id")
        contribution_class = definition.fixed_contribution_class or self._string_field(
            source.payload,
            "contribution_class",
        )
        if (
            contribution_class is not None
            and contribution_class not in ALLOWED_CONTRIBUTION_CLASSES
        ):
            raise AnalyticsProjectionError(
                f"unsupported contribution_class: {contribution_class}"
            )

        payload = {
            key: deepcopy(source.payload[key])
            for key in sorted(definition.allowed_payload_fields)
            if key in source.payload
        }
        event = AnalyticsEvent(
            id=uuid5(
                NAMESPACE_URL,
                (
                    f"kefe-analytics:{source.id}:"
                    f"{definition.analytics_name}:{definition.analytics_version}"
                ),
            ),
            source_event_id=source.id,
            source_event_name=source.event_name,
            source_event_version=source.event_version,
            analytics_name=definition.analytics_name,
            analytics_version=definition.analytics_version,
            occurred_at=source.occurred_at,
            producer_version=self._producer_version,
            actor_id=actor_id,
            session_id=source.aggregate_id,
            case_version_id=case_version_id,
            contribution_class=contribution_class,
            privacy_class=definition.privacy_class,
            retention_class=definition.retention_class,
            metric_families=definition.metric_families,
            payload=payload,
        )
        self._validate_required(event, definition.required_provenance)
        return event

    @classmethod
    def _reject_forbidden(cls, value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                normalized = str(key).strip().lower()
                if normalized in FORBIDDEN_PAYLOAD_KEYS:
                    raise AnalyticsProjectionError(
                        f"forbidden analytics payload field: {normalized}"
                    )
                cls._reject_forbidden(child)
            return
        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            for child in value:
                cls._reject_forbidden(child)

    @staticmethod
    def _uuid_field(payload: Mapping[str, Any], key: str) -> UUID | None:
        value = payload.get(key)
        if value is None:
            return None
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise AnalyticsProjectionError(f"invalid {key}") from exc

    @staticmethod
    def _string_field(payload: Mapping[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _validate_required(event: AnalyticsEvent, required: frozenset[str]) -> None:
        values = {
            "actor_id": event.actor_id,
            "session_id": event.session_id,
            "case_version_id": event.case_version_id,
            "contribution_class": event.contribution_class,
        }
        missing = sorted(name for name in required if values.get(name) is None)
        if missing:
            raise AnalyticsProjectionError(
                "missing required analytics provenance: " + ", ".join(missing)
            )

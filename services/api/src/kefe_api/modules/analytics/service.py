from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from kefe_api.modules.analytics.models import AnalyticsEvent
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

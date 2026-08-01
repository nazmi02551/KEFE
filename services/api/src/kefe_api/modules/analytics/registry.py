from __future__ import annotations

from dataclasses import dataclass

from kefe_api.modules.analytics.models import (
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)


@dataclass(frozen=True, slots=True)
class AnalyticsEventDefinition:
    source_event_name: str
    source_event_version: int
    analytics_name: str
    analytics_version: int
    privacy_class: AnalyticsPrivacyClass
    retention_class: AnalyticsRetentionClass
    metric_families: tuple[str, ...]
    allowed_payload_fields: frozenset[str]
    required_provenance: frozenset[str]
    fixed_contribution_class: str | None = None


AnalyticsRegistry = dict[tuple[str, int], AnalyticsEventDefinition]


def default_analytics_registry() -> AnalyticsRegistry:
    product = AnalyticsPrivacyClass.PRODUCT_ANALYTICS
    retention = AnalyticsRetentionClass.STANDARD_13_MONTHS
    definitions = (
        AnalyticsEventDefinition(
            source_event_name="weigh.started",
            source_event_version=1,
            analytics_name="activation.weigh_started",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("ACTIVATION",),
            allowed_payload_fields=frozenset(),
            required_provenance=frozenset({"actor_id", "session_id", "case_version_id"}),
        ),
        AnalyticsEventDefinition(
            source_event_name="weigh.committed",
            source_event_version=1,
            analytics_name="activation.weigh_committed",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("ACTIVATION", "QUALITY"),
            allowed_payload_fields=frozenset({"committed_at", "has_reason"}),
            required_provenance=frozenset(
                {"actor_id", "session_id", "case_version_id", "contribution_class"}
            ),
            fixed_contribution_class="CORE_PRE_RESULT",
        ),
        AnalyticsEventDefinition(
            source_event_name="result.revealed",
            source_event_version=1,
            analytics_name="activation.result_revealed",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("ACTIVATION",),
            allowed_payload_fields=frozenset({"layer"}),
            required_provenance=frozenset({"session_id", "case_version_id"}),
        ),
        AnalyticsEventDefinition(
            source_event_name="perspective.viewed",
            source_event_version=1,
            analytics_name="quality.perspective_viewed",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("QUALITY",),
            allowed_payload_fields=frozenset({"mode", "card_count"}),
            required_provenance=frozenset({"session_id", "case_version_id"}),
        ),
        AnalyticsEventDefinition(
            source_event_name="exposure.recorded",
            source_event_version=1,
            analytics_name="quality.exposure_recorded",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("QUALITY",),
            allowed_payload_fields=frozenset(
                {"flow_step_code", "resource_category", "exposure_id", "intervention_id"}
            ),
            required_provenance=frozenset({"session_id"}),
        ),
        AnalyticsEventDefinition(
            source_event_name="intervention.exposed",
            source_event_version=1,
            analytics_name="quality.intervention_exposed",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("QUALITY",),
            allowed_payload_fields=frozenset(
                {"flow_step_code", "resource_category", "exposure_id", "intervention_id"}
            ),
            required_provenance=frozenset({"session_id"}),
        ),
        AnalyticsEventDefinition(
            source_event_name="decision.revised",
            source_event_version=1,
            analytics_name="quality.decision_revised",
            analytics_version=1,
            privacy_class=product,
            retention_class=retention,
            metric_families=("QUALITY",),
            allowed_payload_fields=frozenset(
                {"revision_id", "revision_no", "flow_step_code", "delta_id"}
            ),
            required_provenance=frozenset({"session_id"}),
        ),
    )
    return {(item.source_event_name, item.source_event_version): item for item in definitions}

from __future__ import annotations

from kefe_api.modules.decision.dynamic_agenda_thresholding import (
    AgendaPriorityTier,
    DynamicAgendaResult,
    DynamicAgendaThresholdingService,
)


def test_dynamic_agenda_surfaces_national_urgency() -> None:
    r = DynamicAgendaThresholdingService.evaluate_topic(
        topic_id="top_001",
        topic_title="Yapay Zeka Telif Hakları ve Veri Güvenliği Yasası",
        resonance_velocity_index=0.85,
        viewpoint_diversity_entropy=0.80,
    )

    assert isinstance(r, DynamicAgendaResult)
    assert r.priority_tier == AgendaPriorityTier.NATIONAL_URGENCY_SPIKE
    assert r.is_featured_on_national_ballot is True
    assert r.resonance_velocity_index == 0.85


def test_dynamic_agenda_invalid_title() -> None:
    failed = False
    try:
        DynamicAgendaThresholdingService.evaluate_topic(
            topic_id="top_002",
            topic_title="Kısa",  # < 5
            resonance_velocity_index=1.50,  # > 1.0
            viewpoint_diversity_entropy=-0.2,  # < 0.0
        )
    except ValueError:
        failed = True

    assert failed is True

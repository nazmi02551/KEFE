from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.decision.context_drift import (
    ContextDriftNotice,
    ContextDriftService,
    ContextDriftType,
    DriftRecommendedAction,
)


def test_publish_and_retrieve_context_drift_notices() -> None:
    service = ContextDriftService()
    case_version_id = uuid4()
    effective_date = datetime.now(UTC) - timedelta(days=15)

    notice = service.publish_notice(
        case_version_id=case_version_id,
        drift_type=ContextDriftType.LEGAL_REFORM,
        effective_date=effective_date,
        summary="İlgili kanun maddesi TBMM genel kurulunda değiştirilmiş ve yeni tarife düzenlemesi Resmi Gazetede yayımlanmıştır.",
        recommended_action=DriftRecommendedAction.CONTINUE_WITH_AWARENESS,
        source_reference_url="https://resmigazete.gov.tr/2026/08/30",
    )

    assert isinstance(notice, ContextDriftNotice)
    assert notice.drift_type == ContextDriftType.LEGAL_REFORM
    assert notice.recommended_action == DriftRecommendedAction.CONTINUE_WITH_AWARENESS

    notices = service.get_notices_for_case(case_version_id)
    assert len(notices) == 1
    assert notices[0].source_reference_url == "https://resmigazete.gov.tr/2026/08/30"

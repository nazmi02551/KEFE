from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.signal.card_models import (
    SignalConfidenceTier,
    SignalConsensusCardItem,
)
from kefe_api.modules.signal.card_service import SignalConsensusCardService


def test_compose_signal_consensus_card_assigns_correct_tiers() -> None:
    signal_id = uuid4()
    case_id = uuid4()

    # 1. Gold Tier (n=1200, 80%)
    gold_card = SignalConsensusCardService.compose_card(
        signal_id=signal_id,
        case_version_id=case_id,
        case_title="Çocuk Güvenliği ve Sosyal Medya Düzenlemesi",
        consensus_statement="16 yaş altı kullanıcılar için gece erişim kısıtlaması uygulanmalıdır.",
        agreement_percentage=80.5,
        sample_size=1200,
    )
    assert isinstance(gold_card, SignalConsensusCardItem)
    assert gold_card.confidence_tier == SignalConfidenceTier.GOLD
    assert gold_card.agreement_percentage == 80.5

    # 2. Silver Tier (n=600, 68%)
    silver_card = SignalConsensusCardService.compose_card(
        signal_id=signal_id,
        case_version_id=case_id,
        case_title="Gece Ulaşım Seferleri",
        consensus_statement="Hafta sonu gece seferleri artırılmalıdır.",
        agreement_percentage=68.0,
        sample_size=600,
    )
    assert silver_card.confidence_tier == SignalConfidenceTier.SILVER

    # 3. Bronze Tier (n=150, 55%)
    bronze_card = SignalConsensusCardService.compose_card(
        signal_id=signal_id,
        case_version_id=case_id,
        case_title="Yerel Park Alanı Kullanımı",
        consensus_statement="Evcil hayvan alanı genişletilmelidir.",
        agreement_percentage=55.0,
        sample_size=150,
    )
    assert bronze_card.confidence_tier == SignalConfidenceTier.BRONZE


def test_insufficient_sample_size_rejected() -> None:
    failed = False
    try:
        SignalConsensusCardService.compose_card(
            signal_id=uuid4(),
            case_version_id=uuid4(),
            case_title="Başlık",
            consensus_statement="Açıklama",
            agreement_percentage=90.0,
            sample_size=50,  # < 100
        )
    except ValueError:
        failed = True
    assert failed is True

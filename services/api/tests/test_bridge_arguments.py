from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.bridge_models import BridgeArgumentItem
from kefe_api.modules.decision.bridge_service import BridgeArgumentsService


def test_register_and_retrieve_bridge_arguments() -> None:
    service = BridgeArgumentsService()
    case_version_id = uuid4()

    item = service.register_bridge_argument(
        case_version_id=case_version_id,
        synthesis_thesis="Hem şeffaflık hem de veri mahremiyeti kademeli anonimleştirme ile korunabilir.",
        connecting_values=("seffaflik", "mahremiyet", "kamu_yarari"),
        cross_group_support_rate=0.58,
        sample_size=150,
    )

    assert isinstance(item, BridgeArgumentItem)
    assert item.cross_group_support_rate == 0.58
    assert len(item.connecting_values) == 3

    bridges = service.get_bridge_arguments(case_version_id)
    assert len(bridges) == 1
    assert bridges[0].synthesis_thesis.startswith("Hem şeffaflık")


def test_bridge_arguments_guard_minimum_sample_and_rate() -> None:
    service = BridgeArgumentsService()
    case_version_id = uuid4()

    # Sample size < 30 rejected
    failed_sample = False
    try:
        service.register_bridge_argument(
            case_version_id=case_version_id,
            synthesis_thesis="Yetersiz örneklem.",
            connecting_values=("deger",),
            cross_group_support_rate=0.50,
            sample_size=15,
        )
    except ValueError:
        failed_sample = True
    assert failed_sample is True

    # Rate < 0.35 rejected
    failed_rate = False
    try:
        service.register_bridge_argument(
            case_version_id=case_version_id,
            synthesis_thesis="Yetersiz uzlaşı.",
            connecting_values=("deger",),
            cross_group_support_rate=0.20,
            sample_size=50,
        )
    except ValueError:
        failed_rate = True
    assert failed_rate is True

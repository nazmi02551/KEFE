from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.modules.decision.bridge_models import BridgeArgumentItem

MINIMUM_BRIDGE_SAMPLE_SIZE = 30
MINIMUM_CROSS_GROUP_RATE = 0.35


class BridgeArgumentsService:
    def __init__(self) -> None:
        self._bridges_by_case: dict[UUID, list[BridgeArgumentItem]] = {}

    def register_bridge_argument(
        self,
        *,
        case_version_id: UUID,
        synthesis_thesis: str,
        connecting_values: tuple[str, ...],
        cross_group_support_rate: float,
        sample_size: int,
    ) -> BridgeArgumentItem:
        if sample_size < MINIMUM_BRIDGE_SAMPLE_SIZE:
            raise ValueError(
                f"sample_size must be >= {MINIMUM_BRIDGE_SAMPLE_SIZE} for privacy & statistical validity"
            )

        if not (0.0 <= cross_group_support_rate <= 1.0):
            raise ValueError("cross_group_support_rate must be between 0.0 and 1.0")

        if cross_group_support_rate < MINIMUM_CROSS_GROUP_RATE:
            raise ValueError(
                f"cross_group_support_rate must be >= {MINIMUM_CROSS_GROUP_RATE} to qualify as bridge argument"
            )

        item = BridgeArgumentItem(
            bridge_id=uuid4(),
            case_version_id=case_version_id,
            synthesis_thesis=synthesis_thesis.strip(),
            connecting_values=connecting_values,
            cross_group_support_rate=round(cross_group_support_rate, 4),
            sample_size=sample_size,
            created_at=datetime.now(UTC),
        )

        self._bridges_by_case.setdefault(case_version_id, []).append(item)
        return item

    def get_bridge_arguments(self, case_version_id: UUID) -> list[BridgeArgumentItem]:
        return list(self._bridges_by_case.get(case_version_id, []))

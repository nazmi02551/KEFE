from __future__ import annotations

from datetime import datetime
from typing import Protocol

from kefe_api.modules.content_supply_health.models import (
    ContentSupplyOperationalFacts,
)


class ContentSupplyOperationalFactsRepository(Protocol):
    def read_facts(
        self,
        *,
        as_of: datetime,
        failure_window_seconds: int,
    ) -> ContentSupplyOperationalFacts: ...

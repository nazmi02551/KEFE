from __future__ import annotations


class UnavailableCaseMediaDeliveryGate:
    """Fail-closed gate used until a real provider resolver is configured."""

    def permits(self, delivery_ref: str) -> bool:
        del delivery_ref
        return False

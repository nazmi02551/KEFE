from __future__ import annotations

from dataclasses import dataclass, field

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import OtpChannel


class DisabledOtpDelivery:
    def send(self, *, channel: OtpChannel, identifier: str, code: str) -> None:
        del channel, identifier, code
        raise DomainError(
            "AUTH_OTP_DELIVERY_UNAVAILABLE",
            "OTP delivery is not configured",
            503,
            retryable=True,
        )


@dataclass(slots=True)
class CapturingOtpDelivery:
    """Development/test adapter. Never expose captured codes through HTTP."""

    deliveries: dict[tuple[str, str], str] = field(default_factory=dict)

    def send(self, *, channel: OtpChannel, identifier: str, code: str) -> None:
        self.deliveries[(channel.value, identifier)] = code

    def code_for(self, *, channel: OtpChannel, identifier: str) -> str | None:
        return self.deliveries.get((channel.value, identifier))

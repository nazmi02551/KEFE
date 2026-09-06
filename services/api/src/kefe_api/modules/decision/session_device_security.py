from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ClientPlatform(StrEnum):
    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB_BROWSER = "WEB_BROWSER"
    DESKTOP_CLIENT = "DESKTOP_CLIENT"


class DeviceTrustTier(StrEnum):
    HARDWARE_ATTESTED_SECURE = "HARDWARE_ATTESTED_SECURE"
    STANDARD_AUTHENTICATED = "STANDARD_AUTHENTICATED"
    UNRECOGNIZED_STALE = "UNRECOGNIZED_STALE"


@dataclass(frozen=True, slots=True)
class SessionDeviceResult:
    session_id: str
    device_name: str
    client_platform: ClientPlatform
    trust_tier: DeviceTrustTier
    ip_country_code: str
    is_current_device: bool


class SessionDeviceSecurityService:
    @staticmethod
    def register_session(
        *,
        session_id: str,
        device_name: str,
        client_platform: ClientPlatform,
        trust_tier: DeviceTrustTier,
        ip_country_code: str,
        is_current_device: bool,
    ) -> SessionDeviceResult:
        if len(device_name.strip()) < 3:
            raise ValueError("device_name must have at least 3 characters")
        if len(ip_country_code.strip()) != 2:
            raise ValueError("ip_country_code must be ISO 2-letter code")

        return SessionDeviceResult(
            session_id=session_id.strip(),
            device_name=device_name.strip(),
            client_platform=client_platform,
            trust_tier=trust_tier,
            ip_country_code=ip_country_code.strip().upper(),
            is_current_device=is_current_device,
        )

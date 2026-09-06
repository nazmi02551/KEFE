from __future__ import annotations

from kefe_api.modules.decision.session_device_security import (
    ClientPlatform,
    DeviceTrustTier,
    SessionDeviceResult,
    SessionDeviceSecurityService,
)


def test_session_device_registers_current_device() -> None:
    r = SessionDeviceSecurityService.register_session(
        session_id="sess_001",
        device_name="Xiaomi Redmi Note 13 Pro 5G",
        client_platform=ClientPlatform.ANDROID,
        trust_tier=DeviceTrustTier.HARDWARE_ATTESTED_SECURE,
        ip_country_code="TR",
        is_current_device=True,
    )

    assert isinstance(r, SessionDeviceResult)
    assert r.trust_tier == DeviceTrustTier.HARDWARE_ATTESTED_SECURE
    assert r.is_current_device is True
    assert r.ip_country_code == "TR"


def test_session_device_invalid_country() -> None:
    failed = False
    try:
        SessionDeviceSecurityService.register_session(
            session_id="sess_002",
            device_name="Chrome Browser",
            client_platform=ClientPlatform.WEB_BROWSER,
            trust_tier=DeviceTrustTier.STANDARD_AUTHENTICATED,
            ip_country_code="TURKEY",  # != 2
            is_current_device=False,
        )
    except ValueError:
        failed = True

    assert failed is True

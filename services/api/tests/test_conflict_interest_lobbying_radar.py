from __future__ import annotations

from kefe_api.modules.decision.conflict_interest_lobbying_radar import (
    ConflictInterestLobbyingRadarService,
    LobbyingExposureLevel,
    LobbyingRadarResult,
)


def test_lobbying_radar_evaluates_clean_disclosure() -> None:
    r = ConflictInterestLobbyingRadarService.evaluate_organization(
        radar_id="rdr_001",
        organization_id="org_civic_001",
        transparency_index=0.98,
        declared_funding_amount_usd=0.0,
        primary_benefactor_sector="Bağımsız Yurttaş Bağışları",
    )

    assert isinstance(r, LobbyingRadarResult)
    assert r.exposure_level == LobbyingExposureLevel.CLEAN_INDEPENDENT_DISCLOSURE
    assert r.transparency_index == 0.98
    assert r.declared_funding_amount_usd == 0.0


def test_lobbying_radar_invalid_inputs() -> None:
    failed = False
    try:
        ConflictInterestLobbyingRadarService.evaluate_organization(
            radar_id="rdr_002",
            organization_id="org_002",
            transparency_index=1.50,  # > 1.0
            declared_funding_amount_usd=-500.0,  # < 0
            primary_benefactor_sector="AB",  # < 3
        )
    except ValueError:
        failed = True

    assert failed is True

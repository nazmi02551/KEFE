"""Tests for SignalTargetRegistryService.

Updated to use the domain-correct injection pattern:
- SignalTargetRegistryService now takes an InstitutionTargetResolver via __init__.
- Hardcoded institutional targets removed from service; tests inject them via
  StaticInstitutionTargetResolver.
- NullInstitutionTargetResolver returns empty targets (safe default until
  Admin target management is in production — CAP-057).
"""
from datetime import UTC, datetime
from uuid import UUID

import pytest

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    NullInstitutionTargetResolver,
    SignalDispatchError,
    SignalTargetItem,
    SignalTargetRegistryService,
    StaticInstitutionTargetResolver,
    TargetType,
)

_SIGNAL_ID = UUID("77777777-7777-4777-8777-777777777701")
_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
_CERTIFIED_AT = datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC)

_TARGET_PRIMARY = SignalTargetItem(
    target_id=UUID("bbbbbbbb-1111-4bbb-8bbb-111111111111"),
    target_name="İstanbul Büyükşehir Belediyesi Ulaşım Koordinasyon Merkezi (UKOME)",
    target_type=TargetType.MUNICIPAL_GOVERNMENT,
    jurisdiction_level="MUNICIPAL",
    official_contact_channel="ukome.kararlar@ibb.gov.tr",
    dispatch_status=DispatchStatus.ACKNOWLEDGED,
    response_due_days=30,
    dispatched_at=datetime(2026, 8, 16, 9, 0, 0, tzinfo=UTC),
    acknowledged_at=datetime(2026, 8, 18, 14, 20, 0, tzinfo=UTC),
)

_TARGET_SECONDARY = SignalTargetItem(
    target_id=UUID("bbbbbbbb-2222-4bbb-8bbb-222222222222"),
    target_name="T.C. Ulaştırma ve Altyapı Bakanlığı Marmaray Bölge Müdürlüğü",
    target_type=TargetType.MINISTRY_DEPARTMENT,
    jurisdiction_level="REGIONAL",
    official_contact_channel="marmaray.koordinasyon@uab.gov.tr",
    dispatch_status=DispatchStatus.DISPATCHED,
    response_due_days=45,
    dispatched_at=datetime(2026, 8, 16, 9, 15, 0, tzinfo=UTC),
    acknowledged_at=None,
)


def _make_service_with_targets(*targets: SignalTargetItem) -> SignalTargetRegistryService:
    resolver = StaticInstitutionTargetResolver(targets=list(targets))
    return SignalTargetRegistryService(resolver=resolver)


class TestSignalTargetRegistryEvaluation:
    def test_evaluation_with_two_targets(self) -> None:
        service = _make_service_with_targets(_TARGET_PRIMARY, _TARGET_SECONDARY)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
            certified_at=_CERTIFIED_AT,
        )

        assert report.signal_id == _SIGNAL_ID
        assert report.case_version_id == _CASE_VERSION_ID
        assert report.primary_domain_code == "GOVERNANCE"
        assert len(report.targets) == 2
        assert report.primary_target_id == report.targets[0].target_id

    def test_primary_target_is_municipal_acknowledged(self) -> None:
        service = _make_service_with_targets(_TARGET_PRIMARY, _TARGET_SECONDARY)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
            certified_at=_CERTIFIED_AT,
        )

        primary = report.targets[0]
        assert primary.target_type == TargetType.MUNICIPAL_GOVERNMENT
        assert primary.dispatch_status == DispatchStatus.ACKNOWLEDGED
        assert primary.response_due_days == 30
        assert primary.acknowledged_at is not None
        assert "UKOME" in primary.target_name

    def test_secondary_target_is_ministry_dispatched(self) -> None:
        service = _make_service_with_targets(_TARGET_PRIMARY, _TARGET_SECONDARY)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
            certified_at=_CERTIFIED_AT,
        )

        secondary = report.targets[1]
        assert secondary.target_type == TargetType.MINISTRY_DEPARTMENT
        assert secondary.dispatch_status == DispatchStatus.DISPATCHED
        assert secondary.acknowledged_at is None

    def test_proof_hash_is_64_hex_chars(self) -> None:
        service = _make_service_with_targets(_TARGET_PRIMARY, _TARGET_SECONDARY)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
            certified_at=_CERTIFIED_AT,
        )
        assert len(report.registry_proof_hash) == 64

    def test_null_resolver_returns_empty_targets(self) -> None:
        service = SignalTargetRegistryService(resolver=NullInstitutionTargetResolver())
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
            certified_at=_CERTIFIED_AT,
        )
        assert len(report.targets) == 0
        assert report.primary_target_id is None
        assert report.is_fully_dispatched is False

    def test_no_resolver_defaults_to_null(self) -> None:
        service = SignalTargetRegistryService()
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
        )
        assert len(report.targets) == 0


class TestDispatchReportHelpers:
    def test_dispatch_eligible_targets(self) -> None:
        verified = SignalTargetItem(
            target_id=UUID("cccccccc-3333-4ccc-8ccc-333333333333"),
            target_name="Test Kurum",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_channel="test@kurum.gov.tr",
            dispatch_status=DispatchStatus.VERIFIED_TARGET,
            response_due_days=21,
        )
        service = _make_service_with_targets(verified)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
        )
        assert len(report.dispatch_eligible_targets) == 1
        assert report.dispatch_eligible_targets[0].target_id == verified.target_id

    def test_dispatched_targets(self) -> None:
        service = _make_service_with_targets(_TARGET_PRIMARY, _TARGET_SECONDARY)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
        )
        dispatched = report.dispatched_targets
        assert len(dispatched) == 2

    def test_is_fully_dispatched_when_all_terminal(self) -> None:
        declined = SignalTargetItem(
            target_id=UUID("dddddddd-4444-4ddd-8ddd-444444444444"),
            target_name="Declined Kurum",
            target_type=TargetType.CIVIC_OMBUDSMAN,
            jurisdiction_level="LOCAL",
            official_contact_channel="ombudsman@local.gov.tr",
            dispatch_status=DispatchStatus.DECLINED_JURISDICTION,
            response_due_days=0,
        )
        service = _make_service_with_targets(declined)
        report = service.evaluate(
            signal_id=_SIGNAL_ID,
            case_version_id=_CASE_VERSION_ID,
            primary_domain_code="GOVERNANCE",
        )
        assert report.is_fully_dispatched is True


class TestDispatchTransitionValidation:
    def test_valid_transition_verified_to_dispatched(self) -> None:
        target = SignalTargetItem(
            target_id=UUID("eeeeeeee-5555-4eee-8eee-555555555555"),
            target_name="Valid Target",
            target_type=TargetType.REGULATORY_BODY,
            jurisdiction_level="NATIONAL",
            official_contact_channel="contact@reg.gov.tr",
            dispatch_status=DispatchStatus.VERIFIED_TARGET,
            response_due_days=30,
        )
        # Should not raise
        SignalTargetRegistryService.validate_transition(
            target, DispatchStatus.DISPATCHED
        )

    def test_invalid_transition_dispatched_to_proposed_raises(self) -> None:
        target = SignalTargetItem(
            target_id=UUID("ffffffff-6666-4fff-8fff-666666666666"),
            target_name="Dispatched Target",
            target_type=TargetType.MUNICIPAL_GOVERNMENT,
            jurisdiction_level="MUNICIPAL",
            official_contact_channel="contact@mun.gov.tr",
            dispatch_status=DispatchStatus.DISPATCHED,
            response_due_days=30,
        )
        with pytest.raises(SignalDispatchError, match="Cannot transition"):
            SignalTargetRegistryService.validate_transition(
                target, DispatchStatus.PROPOSED_TARGET
            )

    def test_terminal_status_action_pledged_no_transitions(self) -> None:
        target = SignalTargetItem(
            target_id=UUID("aaaaaaaa-7777-4aaa-8aaa-777777777777"),
            target_name="Pledged Target",
            target_type=TargetType.MINISTRY_DEPARTMENT,
            jurisdiction_level="NATIONAL",
            official_contact_channel="contact@min.gov.tr",
            dispatch_status=DispatchStatus.ACTION_PLEDGED,
            response_due_days=60,
        )
        with pytest.raises(SignalDispatchError):
            SignalTargetRegistryService.validate_transition(
                target, DispatchStatus.DISPATCHED
            )


class TestEnumValues:
    def test_target_type_values(self) -> None:
        assert TargetType.MUNICIPAL_GOVERNMENT.value == "MUNICIPAL_GOVERNMENT"
        assert TargetType.REGULATORY_BODY.value == "REGULATORY_BODY"
        assert TargetType.CIVIC_OMBUDSMAN.value == "CIVIC_OMBUDSMAN"

    def test_dispatch_status_values(self) -> None:
        assert DispatchStatus.DISPATCHED.value == "DISPATCHED"
        assert DispatchStatus.ACTION_PLEDGED.value == "ACTION_PLEDGED"
        assert DispatchStatus.DECLINED_JURISDICTION.value == "DECLINED_JURISDICTION"
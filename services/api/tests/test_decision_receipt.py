from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from kefe_api.modules.decision.decision_receipt import (
    DecisionReceiptGenerator,
    DecisionReceiptResult,
)


def test_decision_receipt_generator_produces_valid_digest() -> None:
    case_id = uuid4()
    ts = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)

    r = DecisionReceiptGenerator.generate(
        case_version_id=case_id,
        committed_choice="SEÇENEK_A_KAMU_YARARI",
        user_pseudonym="user_anon_94812",
        timestamp=ts,
    )

    assert isinstance(r, DecisionReceiptResult)
    assert r.receipt_id.startswith("kefe-rcpt-")
    assert len(r.integrity_digest) == 64
    assert r.committed_choice == "SEÇENEK_A_KAMU_YARARI"


def test_decision_receipt_invalid_input() -> None:
    case_id = uuid4()
    failed = False
    try:
        DecisionReceiptGenerator.generate(
            case_version_id=case_id,
            committed_choice="",
            user_pseudonym="abc",
        )
    except ValueError:
        failed = True

    assert failed is True

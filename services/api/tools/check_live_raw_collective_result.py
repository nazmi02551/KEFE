from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/live-raw-collective-result.v1.json"
RAW_ADAPTER = ROOT / "services/api/src/kefe_api/infrastructure/postgres_live_raw_decision.py"
REASON_ADAPTER = ROOT / "services/api/src/kefe_api/infrastructure/postgres_reason_decision.py"
MOBILE_MODEL = ROOT / "apps/mobile/lib/features/decision/domain/decision_models.dart"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} is missing required boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden dependency: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-LIVE-RAW-COLLECTIVE-RESULT-001":
        raise SystemExit("unexpected live RAW contract id")
    if contract["selection_policy"]["trusted_snapshot_precedence"] is not True:
        raise SystemExit("TRUSTED snapshot precedence must remain explicit")
    if contract["methodology_boundary"]["confidence_label"] != "INSUFFICIENT":
        raise SystemExit("RAW must not fabricate a statistical confidence label")
    if contract["persistence"]["raw_snapshot_persisted"] is not False:
        raise SystemExit("this F4 slice must not persist RAW snapshots")
    if contract["api"]["response_shape_changed"] is not False:
        raise SystemExit("this slice must preserve the reveal HTTP shape")

    raw = RAW_ADAPTER.read_text(encoding="utf-8")
    reason = REASON_ADAPTER.read_text(encoding="utf-8")
    mobile = MOBILE_MODEL.read_text(encoding="utf-8")

    for needle in (
        "trusted = super().get_reveal(case_version_id)",
        "if trusted is not None:",
        "AND qv.response_type = 'SINGLE_CHOICE'",
        "AND qv.is_required = true",
        "ORDER BY i.sort_order, q.sort_order, q.id",
        "AND ws.state = 'COMMITTED'",
        "layer=\"RAW\"",
        "confidence=\"INSUFFICIENT\"",
        "counts.get(option, 0) / sample_size",
    ):
        require(raw, needle, where="RAW adapter")

    for forbidden in (
        "decision.private_reason",
        "demograph",
        "country",
        "device",
        "trust_score",
        "bot_score",
        "analytics.result_snapshot (",
        "INSERT INTO analytics.result_snapshot",
        "UPDATE analytics.result_snapshot",
    ):
        forbid(raw.lower(), forbidden.lower(), where="RAW adapter")

    require(
        reason,
        "class PostgresReasonDecisionRepository(PostgresLiveRawDecisionRepository):",
        where="PostgreSQL decision composition",
    )
    require(
        reason,
        "from kefe_api.infrastructure.postgres_live_raw_decision import",
        where="PostgreSQL decision composition",
    )

    require(mobile, "final String layer;", where="mobile RevealResult")
    forbid(mobile, "enum RevealLayer", where="mobile RevealResult")

    print("live RAW Collective Result contract: OK")


if __name__ == "__main__":
    main()

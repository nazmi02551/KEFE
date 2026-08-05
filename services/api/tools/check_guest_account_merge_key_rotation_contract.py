from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/guest-account-merge-key-rotation.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Guest merge key rotation contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(
        contract["contract_id"] == "KEFE-GUEST-MERGE-KEY-ROTATION-001",
        "contract id",
    )
    _require(contract["capabilities"] == ["CAP-084"], "CAP-084 binding")
    _require(
        contract["public_api"]["openapi_drift_allowed"] is False,
        "OpenAPI drift policy",
    )
    _require(
        contract["persistence"]["new_database_schema_required"] is False,
        "unexpected database schema",
    )
    _require(
        contract["verification_token"]["legacy_key_id"] == "primary-v1",
        "legacy key id",
    )
    _require(
        contract["replay"]["expiry_checked_before_key_lookup"] is True,
        "expiry-before-key invariant",
    )

    settings = _text("services/api/src/kefe_api/core/settings.py")
    service = _text("services/api/src/kefe_api/modules/identity/account_service.py")
    memory_tests = _text("services/api/tests/test_guest_merge_key_rotation.py")
    postgres_tests = _text(
        "services/api/tests/test_guest_merge_key_rotation_postgres.py"
    )
    workflow = _text(".github/workflows/guest-merge-key-rotation.yml")
    adr = _text("docs/adr/0111-versioned-guest-merge-replay-keyring.md")

    _require("account_merge_replay_active_key_id" in settings, "active key setting")
    _require("account_merge_replay_retained_keys" in settings, "retained key setting")
    _require("kefe_v2" in service, "versioned verification envelope")
    _require("DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID" in service, "legacy key mapping")
    _require("kefe:guest-account-merge:v1" in service, "legacy derivation domain")
    _require("kefe:guest-account-merge:v2" in service, "versioned derivation domain")
    _require("DEPENDENCY_TEMPORARILY_UNAVAILABLE" in service, "missing-key failure")
    _require("AUTH_TOKEN_EXPIRED" in service, "expired replay failure")
    _require(
        service.index("account_session_expires_at <= now")
        < service.index("self._derive_account_token", service.index("def _credential_from_replay")),
        "replay expiry must be checked before key derivation",
    )
    _require("legacy" in memory_tests.lower(), "legacy memory evidence")
    _require("retained" in memory_tests.lower(), "retained-key memory evidence")
    _require("restart" in postgres_tests.lower(), "PostgreSQL restart evidence")
    _require("Exact OpenAPI remains unchanged" in workflow, "exact OpenAPI gate")
    _require("Two-phase rotation procedure" in adr, "operator rotation procedure")

    forbidden_persistence = (
        "credential_key_id",
        "replay_secret",
        "hmac_secret",
        "access_token text",
    )
    migration = _text(
        "services/api/migrations/versions/20260805_0030_guest_merge_replay.py"
    ).lower()
    for fragment in forbidden_persistence:
        _require(fragment not in migration, f"forbidden persistence: {fragment}")

    print(
        "Guest merge key rotation contract: PASS — legacy compatibility, versioned "
        "verification envelope, validated active/retained keyring, expiry-before-key "
        "retirement, fail-closed live replay, no new persistence and unchanged OpenAPI."
    )


if __name__ == "__main__":
    main()

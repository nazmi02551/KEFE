from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/guest-account-merge-replay.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Guest account merge replay contract: FAIL — {message}")


def _text(relative_path: str) -> str:
    path = ROOT / relative_path
    _require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _require(contract["contract_id"] == "KEFE-GUEST-ACCOUNT-MERGE-REPLAY-001", "contract id")
    _require(contract["capabilities"] == ["CAP-084"], "CAP-084 binding")
    _require(contract["public_api"]["request_schema_changed"] is False, "request drift")
    _require(contract["public_api"]["response_schema_changed"] is False, "response drift")
    _require(contract["credential"]["plaintext_persisted"] is False, "plaintext credential")
    _require(contract["postgres_transaction"]["all_or_nothing"] is True, "atomicity")

    models = _text("services/api/src/kefe_api/modules/identity/account_models.py")
    ports = _text("services/api/src/kefe_api/modules/identity/account_ports.py")
    service = _text("services/api/src/kefe_api/modules/identity/account_service.py")
    router = _text("services/api/src/kefe_api/modules/identity/account_router.py")
    identity_service = _text("services/api/src/kefe_api/modules/identity/service.py")
    memory = _text("services/api/src/kefe_api/modules/identity/account_in_memory.py")
    postgres = _text("services/api/src/kefe_api/infrastructure/postgres_account_continuity.py")
    postgres_identity = _text("services/api/src/kefe_api/infrastructure/postgres_identity.py")
    settings = _text("services/api/src/kefe_api/core/settings.py")
    migration = _text(
        "services/api/migrations/versions/20260805_0030_guest_merge_replay.py"
    )

    _require("GuestMergeReplay" in models, "typed replay model")
    _require("complete_guest_merge" in ports, "atomic repository port")
    _require("complete_guest_merge" in memory, "memory replay implementation")
    _require("complete_guest_merge" in postgres, "PostgreSQL replay implementation")
    _require("guest_merge_replay" in migration, "durable replay table")
    _require("verification_token_hash" in migration, "verification hash replay key")
    _require("access_token" not in migration, "migration must not persist plaintext token")
    _require("ON DELETE CASCADE" in migration, "verification-linked privacy cleanup")
    _require("account_merge_replay_secret" in settings, "HMAC secret setting")
    _require("hmac.new" in service, "HMAC credential derivation")
    _require("kefe:guest-account-merge:v1" in service, "domain separation")
    _require("authenticate_guest_merge" in identity_service, "narrow replay authorization")
    _require("authenticate_guest_merge" in router, "router uses narrow authorization")
    _require("TokenStatus.REVOKED" in postgres_identity, "revoked principal resolution")

    forbidden_fragments = (
        "access_token text",
        "access_token varchar",
        "verification_token text",
        "otp_code text",
    )
    combined_persistence = f"{migration}\n{postgres}"
    for fragment in forbidden_fragments:
        _require(fragment not in combined_persistence.lower(), f"forbidden persistence: {fragment}")

    print(
        "Guest account merge replay contract: PASS — natural verification replay key, "
        "HMAC credential reconstruction, atomic persistence, narrow revoked-token replay, "
        "privacy cascade, and unchanged public schema."
    )


if __name__ == "__main__":
    main()

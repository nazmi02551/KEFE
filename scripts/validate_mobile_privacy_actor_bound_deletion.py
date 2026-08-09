from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/mobile-privacy-actor-bound-deletion.v1.json"
SERVER_SERVICE = ROOT / "services/api/src/kefe_api/modules/privacy/service.py"
DECISION_REPO = ROOT / "apps/mobile/lib/features/decision/data/http_decision_repository.dart"
ACCOUNT_REPO = ROOT / "apps/mobile/lib/features/account/data/http_account_repository.dart"
PRIVACY_REPO = ROOT / "apps/mobile/lib/features/privacy/data/http_privacy_repository.dart"
SECURE_STORE = ROOT / "apps/mobile/lib/core/storage/secure_credential_store.dart"
TEST = ROOT / "apps/mobile/test/mobile_privacy_actor_bound_delete_test.dart"
FORBIDDEN_WORKFLOW = ROOT / ".github/workflows/mobile-privacy-actor-bound-delete.yml"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing required privacy boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden privacy behavior: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-MOBILE-PRIVACY-ACTOR-BOUND-DELETION-001":
        raise SystemExit("unexpected mobile privacy deletion contract id")
    if contract["problem"]["bearer_token_is_opaque"] is not True:
        raise SystemExit("bearer token must remain opaque")
    if contract["credential_continuity"]["persisted_store_is_mobile_bearer_source_of_truth"] is not True:
        raise SystemExit("persisted credential store must remain bearer source of truth")
    if contract["credential_continuity"]["decision_repository_bearer_cache_allowed"] is not False:
        raise SystemExit("parallel DecisionRepository bearer cache must remain forbidden")
    if contract["legacy_compatibility"]["server_confirmation_requirement_may_be_weakened"] is not False:
        raise SystemExit("server destructive confirmation must not be weakened")
    if contract["deletion_request"]["plain_delete_allowed"] is not False:
        raise SystemExit("plain DELETE confirmation must remain forbidden")
    if contract["architecture"]["new_github_actions_workflow_allowed"] is not False:
        raise SystemExit("feature-specific workflow growth must remain disabled")
    if FORBIDDEN_WORKFLOW.exists():
        raise SystemExit("mobile privacy deletion slice must use existing Mobile CI")

    server = SERVER_SERVICE.read_text(encoding="utf-8")
    decision = DECISION_REPO.read_text(encoding="utf-8")
    account = ACCOUNT_REPO.read_text(encoding="utf-8")
    privacy = PRIVACY_REPO.read_text(encoding="utf-8")
    secure = SECURE_STORE.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    require(server, 'expected = f"DELETE:{principal.actor_id}"', where="privacy service")
    require(server, "hmac.compare_digest(confirmation, expected)", where="privacy service")

    for needle in (
        "Future<String?> readActorId();",
        "Future<void> writeActorId(String actorId);",
        "final existing = await _credentialStore.read();",
        "await _credentialStore.writeActorId(credential.actorId);",
        "actorId: await _credentialStore.readActorId() ?? ''",
    ):
        require(decision, needle, where="mobile credential/guest repository")
    forbid(decision, "String? _token;", where="DecisionRepository credential state")
    forbid(decision, "_token =", where="DecisionRepository credential state")

    require(account, "await _credentialStore.writeActorId(actorId);", where="account merge")

    for needle in (
        "static const _actorIdKey = 'kefe.actor_id.v1'",
        "_storage.delete(key: _actorIdKey)",
        "Future<String?> readActorId()",
        "Future<void> writeActorId(String actorId)",
    ):
        require(secure, needle, where="secure credential store")

    for needle in (
        "final actorId = await _resolveActorId();",
        "'X-KEFE-Delete-Confirm': 'DELETE:$actorId'",
        "await export();",
        "data['actor_id']",
        "body['actor_id'] != actorId",
        "body['private_data_deleted'] != true",
        "body['aggregate_contributions_anonymized'] != true",
        "DateTime.tryParse(deletedAt)",
        "PRIVACY_DELETE_RECEIPT_INVALID",
        "await _credentialStore.clear();",
    ):
        require(privacy, needle, where="mobile privacy repository")
    forbid(
        privacy,
        "'X-KEFE-Delete-Confirm': 'DELETE',",
        where="mobile privacy repository",
    )
    receipt_check = privacy.find("body['actor_id'] != actorId")
    receipt_parse = privacy.find("DateTime.tryParse(deletedAt)")
    clear_call = privacy.find("await _credentialStore.clear();")
    if (
        receipt_check < 0
        or receipt_parse < 0
        or clear_call < 0
        or clear_call <= receipt_check
        or clear_call <= receipt_parse
    ):
        raise SystemExit("credentials must be cleared only after complete receipt validation")

    for needle in (
        "guest issuance persists opaque token and actor id separately",
        "persisted account credential replaces guest credential without restart",
        "cleared credential store forces fresh guest issuance in same process",
        "account merge replaces persisted token and actor id together",
        "privacy delete sends exact actor-bound confirmation then clears",
        "legacy token resolves actor id through authenticated export once",
        "mismatched deletion receipt fails closed and keeps credentials",
        "false deletion flags fail closed and keep credentials",
        "malformed deletion receipt fails closed and keeps credentials",
        "'DELETE:$accountActorId'",
        "PRIVACY_DELETE_RECEIPT_INVALID",
    ):
        require(test, needle, where="mobile privacy repository tests")

    print("Mobile privacy actor-bound deletion: OK")


if __name__ == "__main__":
    main()

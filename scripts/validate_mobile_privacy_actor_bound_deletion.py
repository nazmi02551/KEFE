from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/mobile-privacy-actor-bound-deletion.v1.json"
SERVER_SERVICE = ROOT / "services/api/src/kefe_api/modules/privacy/service.py"
DECISION_REPO = (
    ROOT / "apps/mobile/lib/features/decision/data/http_decision_repository.dart"
)
ACCOUNT_REPO = (
    ROOT / "apps/mobile/lib/features/account/data/http_account_repository.dart"
)
PRIVACY_REPO = (
    ROOT / "apps/mobile/lib/features/privacy/data/http_privacy_repository.dart"
)
SECURE_STORE = ROOT / "apps/mobile/lib/core/storage/secure_credential_store.dart"
SESSION_STORE = ROOT / "apps/mobile/lib/core/storage/session_credential_store.dart"
BUNDLE = ROOT / "apps/mobile/lib/core/storage/credential_bundle.dart"
STRINGS = ROOT / "apps/mobile/lib/core/localization/internal_alpha_strings.dart"
ERROR_CATALOG = (
    ROOT / "apps/mobile/lib/core/localization/privacy_error_string_catalog.dart"
)
TEST = ROOT / "apps/mobile/test/mobile_privacy_actor_bound_delete_test.dart"
COPY_TEST = ROOT / "apps/mobile/test/privacy_error_copy_test.dart"
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
    if (
        contract["credential_continuity"][
            "persisted_store_is_mobile_bearer_source_of_truth"
        ]
        is not True
    ):
        raise SystemExit(
            "persisted credential store must remain bearer source of truth"
        )
    if (
        contract["credential_continuity"]["decision_repository_bearer_cache_allowed"]
        is not False
    ):
        raise SystemExit(
            "parallel DecisionRepository bearer cache must remain forbidden"
        )
    if (
        contract["legacy_compatibility"][
            "server_confirmation_requirement_may_be_weakened"
        ]
        is not False
    ):
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
    session_store = SESSION_STORE.read_text(encoding="utf-8")
    bundle = BUNDLE.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    error_catalog = ERROR_CATALOG.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    copy_test = COPY_TEST.read_text(encoding="utf-8")

    require(
        server, 'expected = f"DELETE:{principal.actor_id}"', where="privacy service"
    )
    require(
        server, "hmac.compare_digest(confirmation, expected)", where="privacy service"
    )

    for needle in (
        "Future<String?> readActorId();",
        "Future<void> writeActorId(String actorId);",
        "implements AtomicCredentialBundleStore",
    ):
        require(session_store, needle, where="mobile session credential store")

    for needle in (
        "final existing = await _credentialStore.read();",
        "SessionCredentialBundle.fromApiJson(",
        "await _credentialStore.writeBundle(newBundle);",
        "actorId: await _credentialStore.readActorId() ?? ''",
    ):
        require(decision, needle, where="mobile credential/guest repository")

    repository_marker = "class HttpDecisionRepository"
    repository_start = decision.find(repository_marker)
    if repository_start < 0:
        raise SystemExit("mobile decision repository class not found")
    decision_repository = decision[repository_start:]
    forbid(
        decision_repository,
        "String? _token;",
        where="DecisionRepository credential state",
    )
    forbid(
        decision_repository,
        "_token =",
        where="DecisionRepository credential state",
    )

    for needle in (
        "SessionCredentialBundle.fromApiJson(",
        "await _credentialStore.writeBundle(bundle);",
    ):
        require(account, needle, where="account merge")

    for needle in (
        "required this.actorId",
        "required this.actorKind",
        "required this.accessToken",
        "required this.accessExpiresAt",
        "required this.renewalToken",
        "required this.rotationCounter",
    ):
        require(bundle, needle, where="atomic credential bundle")

    for needle in (
        "static const _actorIdKey = 'kefe.actor_id.v1'",
        "static const _bundleKey = 'kefe.session.credential_bundle.v2'",
        "_storage.delete(key: _actorIdKey)",
        "Future<String?> readActorId()",
        "Future<void> writeActorId(String actorId)",
        "Future<void> writeBundle(SessionCredentialBundle bundle)",
        "_storage.write(key: _bundleKey, value: bundle.encode())",
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
        raise SystemExit(
            "credentials must be cleared only after complete receipt validation"
        )

    for needle in (
        "PrivacyErrorStringCatalog.resources",
        "PRIVACY_ACTOR_ID_UNAVAILABLE",
        "PRIVACY_DELETE_RECEIPT_INVALID",
        "_privacyErrorText('receipt_invalid')",
    ):
        require(strings, needle, where="privacy error localization")
    for needle in (
        "'tr':",
        "'en':",
        "silindiği varsayılmadı",
        "not treated as deleted",
        "secure-deletion receipt",
    ):
        require(error_catalog, needle, where="privacy error string catalog")

    for needle in (
        "guest issuance atomically persists the complete credential bundle",
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
    for needle in (
        "Turkish invalid deletion receipt copy hides internal error code",
        "English invalid deletion receipt copy hides internal error code",
        "identity migration error is explicit without leaking code",
        "isNot(contains('PRIVACY_DELETE_RECEIPT_INVALID'))",
    ):
        require(copy_test, needle, where="privacy error copy tests")

    print("Mobile privacy actor-bound deletion: OK")


if __name__ == "__main__":
    main()

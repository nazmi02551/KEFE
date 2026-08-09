import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/features/account/data/http_account_repository.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';
import 'package:kefe_mobile/features/privacy/data/http_privacy_repository.dart';

const config = AppConfig(
  apiBaseUri: Uri(scheme: 'https', host: 'api.example.com'),
  requestTimeout: Duration(seconds: 5),
);

const guestActorId = '11111111-1111-4111-8111-111111111111';
const accountActorId = '22222222-2222-4222-8222-222222222222';
const otherActorId = '33333333-3333-4333-8333-333333333333';
const receiptId = '44444444-4444-4444-8444-444444444444';

http.Response jsonResponse(Map<String, Object?> body, {int status = 200}) =>
    http.Response(
      jsonEncode(body),
      status,
      headers: const {'content-type': 'application/json'},
    );

Map<String, Object?> validDeletionReceipt(String actorId) => {
  'receipt_id': receiptId,
  'actor_id': actorId,
  'actor_kind': 'GUEST',
  'deleted_at': '2026-08-09T09:30:00Z',
  'policy_version': 'PRIVACY_SELF_SERVICE_V2',
  'private_data_deleted': true,
  'aggregate_contributions_anonymized': true,
};

void main() {
  test('guest issuance persists opaque token and actor id separately', () async {
    final store = MemoryCredentialStore();
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/v1/identity/guest');
      return jsonResponse({
        'actor_id': guestActorId,
        'access_token': 'guest-token',
        'expires_at': '2026-09-08T09:30:00Z',
      }, status: 201);
    });
    final repository = HttpDecisionRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    final credential = await repository.ensureGuestCredential();

    expect(credential.actorId, guestActorId);
    expect(await store.read(), 'guest-token');
    expect(await store.readActorId(), guestActorId);
  });

  test('account merge replaces persisted token and actor id together', () async {
    final store = MemoryCredentialStore();
    await store.write('guest-token');
    await store.writeActorId(guestActorId);
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/v1/auth/guest-merge');
      expect(request.headers['authorization'], 'Bearer guest-token');
      return jsonResponse({
        'actor_id': accountActorId,
        'access_token': 'account-token',
        'expires_at': '2026-09-08T09:30:00Z',
        'merged_from_actor_id': guestActorId,
      });
    });
    final repository = HttpAccountRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    final conversion = await repository.mergeGuest(
      verificationToken: 'verification-token-123456',
    );

    expect(conversion.actorId, accountActorId);
    expect(await store.read(), 'account-token');
    expect(await store.readActorId(), accountActorId);
  });

  test('privacy delete sends exact actor-bound confirmation then clears', () async {
    final store = MemoryCredentialStore();
    await store.write('account-token');
    await store.writeActorId(accountActorId);
    var deleteCalls = 0;
    final client = MockClient((request) async {
      expect(request.method, 'DELETE');
      expect(request.url.path, '/v1/me');
      expect(request.headers['authorization'], 'Bearer account-token');
      expect(
        request.headers['x-kefe-delete-confirm'],
        'DELETE:$accountActorId',
      );
      deleteCalls += 1;
      return jsonResponse(validDeletionReceipt(accountActorId));
    });
    final repository = HttpPrivacyRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    final receipt = await repository.delete();

    expect(receipt.receiptId, receiptId);
    expect(deleteCalls, 1);
    expect(await store.read(), isNull);
    expect(await store.readActorId(), isNull);
  });

  test('legacy token resolves actor id through authenticated export once', () async {
    final store = MemoryCredentialStore();
    await store.write('legacy-token');
    final calls = <String>[];
    final client = MockClient((request) async {
      calls.add('${request.method} ${request.url.path}');
      expect(request.headers['authorization'], 'Bearer legacy-token');
      if (request.method == 'GET' &&
          request.url.path == '/v1/me/privacy-export') {
        return jsonResponse({
          'actor_id': guestActorId,
          'schema_version': 'privacy-export.v2',
        });
      }
      if (request.method == 'DELETE' && request.url.path == '/v1/me') {
        expect(
          request.headers['x-kefe-delete-confirm'],
          'DELETE:$guestActorId',
        );
        return jsonResponse(validDeletionReceipt(guestActorId));
      }
      fail('Unexpected request ${request.method} ${request.url}');
    });
    final repository = HttpPrivacyRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    await repository.delete();

    expect(calls, [
      'GET /v1/me/privacy-export',
      'DELETE /v1/me',
    ]);
    expect(await store.read(), isNull);
    expect(await store.readActorId(), isNull);
  });

  test('mismatched deletion receipt fails closed and keeps credentials', () async {
    final store = MemoryCredentialStore();
    await store.write('account-token');
    await store.writeActorId(accountActorId);
    final client = MockClient((request) async {
      return jsonResponse(validDeletionReceipt(otherActorId));
    });
    final repository = HttpPrivacyRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    await expectLater(
      repository.delete(),
      throwsA(
        isA<ApiFailure>().having(
          (error) => error.code,
          'code',
          'PRIVACY_DELETE_RECEIPT_INVALID',
        ),
      ),
    );

    expect(await store.read(), 'account-token');
    expect(await store.readActorId(), accountActorId);
  });

  test('false deletion flags fail closed and keep credentials', () async {
    final store = MemoryCredentialStore();
    await store.write('account-token');
    await store.writeActorId(accountActorId);
    final client = MockClient((request) async {
      final body = validDeletionReceipt(accountActorId);
      body['aggregate_contributions_anonymized'] = false;
      return jsonResponse(body);
    });
    final repository = HttpPrivacyRepository(
      config: config,
      client: client,
      credentialStore: store,
    );

    await expectLater(repository.delete(), throwsA(isA<ApiFailure>()));

    expect(await store.read(), 'account-token');
    expect(await store.readActorId(), accountActorId);
  });
}

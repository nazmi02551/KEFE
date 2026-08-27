import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/core/network/session_renewal_client.dart';
import 'package:kefe_mobile/core/storage/credential_bundle.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';

final config = AppConfig(
  apiBaseUri: Uri.parse('https://api.example.test/'),
  requestTimeout: Duration(seconds: 5),
);

SessionCredentialBundle bundle({
  required DateTime expiresAt,
  String actorKind = 'GUEST',
  String accessToken = 'kefe_g_access_0',
  String renewalToken = 'kefe_r_renewal_0',
  int rotationCounter = 0,
}) => SessionCredentialBundle(
  actorId: 'actor-123',
  actorKind: actorKind,
  accessToken: accessToken,
  accessExpiresAt: expiresAt,
  renewalToken: renewalToken,
  rotationCounter: rotationCounter,
);

Map<String, Object?> bundleBody({
  String actorKind = 'GUEST',
  String accessToken = 'kefe_g_access_1',
  String renewalToken = 'kefe_r_renewal_1',
  int rotationCounter = 1,
}) => {
  'actor_id': 'actor-123',
  'actor_kind': actorKind,
  'access_token': accessToken,
  'access_expires_at': '2026-09-01T12:00:00Z',
  'renewal_token': renewalToken,
  'rotation_counter': rotationCounter,
};

void main() {
  test(
    'proactive renewal is single-flight across concurrent requests',
    () async {
      final now = DateTime.utc(2026, 8, 27, 10);
      final store = MemoryCredentialStore();
      await store.writeBundle(
        bundle(expiresAt: now.add(const Duration(seconds: 30))),
      );
      final release = Completer<void>();
      var renewalRequests = 0;
      final client = MockClient((request) async {
        expect(request.url.path, '/v1/identity/session/renew');
        renewalRequests += 1;
        await release.future;
        return http.Response(jsonEncode(bundleBody()), 200);
      });
      final coordinator = SessionRenewalCoordinator(
        config: config,
        client: client,
        credentialStore: store,
        now: () => now,
      );

      final first = coordinator.ensureCurrent();
      final second = coordinator.ensureCurrent();
      await Future<void>.delayed(Duration.zero);
      expect(renewalRequests, 1);
      release.complete();
      final results = await Future.wait([first, second]);

      expect(results[0]!.accessToken, 'kefe_g_access_1');
      expect(results[1]!.accessToken, results[0]!.accessToken);
      expect((await store.readBundle())!.rotationCounter, 1);
    },
  );

  test(
    'expired access renews once and retries the protected request once',
    () async {
      final now = DateTime.utc(2026, 8, 27, 10);
      final store = MemoryCredentialStore();
      await store.writeBundle(
        bundle(expiresAt: now.add(const Duration(days: 1))),
      );
      var protectedRequests = 0;
      var renewalRequests = 0;
      final inner = MockClient((request) async {
        if (request.url.path == '/v1/identity/session/renew') {
          renewalRequests += 1;
          return http.Response(jsonEncode(bundleBody()), 200);
        }
        protectedRequests += 1;
        if (request.headers['authorization'] == 'Bearer kefe_g_access_0') {
          return http.Response(jsonEncode({'code': 'AUTH_TOKEN_EXPIRED'}), 401);
        }
        expect(request.headers['authorization'], 'Bearer kefe_g_access_1');
        return http.Response(jsonEncode({'ok': true}), 200);
      });
      final coordinator = SessionRenewalCoordinator(
        config: config,
        client: inner,
        credentialStore: store,
        now: () => now,
      );
      final client = RenewingHttpClient(inner: inner, coordinator: coordinator);

      final response = await client.get(
        Uri.parse('https://api.example.test/v1/protected'),
        headers: const {'authorization': 'Bearer kefe_g_access_0'},
      );

      expect(response.statusCode, 200);
      expect(protectedRequests, 2);
      expect(renewalRequests, 1);
    },
  );

  test(
    'active legacy access bootstraps without creating a new actor',
    () async {
      final store = MemoryCredentialStore();
      await store.write('kefe_g_legacy_access');
      await store.writeActorId('actor-123');
      var bootstrapRequests = 0;
      final client = MockClient((request) async {
        expect(request.url.path, '/v1/identity/session/continuity/bootstrap');
        expect(request.headers['authorization'], 'Bearer kefe_g_legacy_access');
        bootstrapRequests += 1;
        return http.Response(jsonEncode(bundleBody(rotationCounter: 0)), 200);
      });
      final coordinator = SessionRenewalCoordinator(
        config: config,
        client: client,
        credentialStore: store,
      );

      final current = await coordinator.ensureCurrent();

      expect(current!.actorId, 'actor-123');
      expect(current.rotationCounter, 0);
      expect(bootstrapRequests, 1);
      expect(await store.read(), current.accessToken);
    },
  );

  test('terminal account renewal failure requires reauthentication', () async {
    final now = DateTime.utc(2026, 8, 27, 10);
    final store = MemoryCredentialStore();
    await store.writeBundle(
      bundle(
        actorKind: 'ACCOUNT',
        accessToken: 'kefe_a_access_0',
        expiresAt: now.add(const Duration(seconds: 30)),
      ),
    );
    final inner = MockClient((request) async {
      expect(request.url.path, '/v1/identity/session/renew');
      return http.Response(
        jsonEncode({'code': 'AUTH_SESSION_CONTINUITY_EXPIRED'}),
        401,
      );
    });
    final coordinator = SessionRenewalCoordinator(
      config: config,
      client: inner,
      credentialStore: store,
      now: () => now,
    );
    final client = RenewingHttpClient(inner: inner, coordinator: coordinator);

    final response = await client.get(
      Uri.parse('https://api.example.test/v1/protected'),
      headers: const {'authorization': 'Bearer kefe_a_access_0'},
    );

    expect(response.statusCode, 401);
    expect(jsonDecode(response.body), {
      'code': 'AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED',
    });
  });

  test(
    'guest continuity failure reaches repository as an explicit API state',
    () async {
      final now = DateTime.utc(2026, 8, 27, 10);
      final store = MemoryCredentialStore();
      await store.writeBundle(
        bundle(expiresAt: now.add(const Duration(seconds: 30))),
      );
      final inner = MockClient((request) async {
        expect(request.url.path, '/v1/identity/session/renew');
        return http.Response(
          jsonEncode({'code': 'AUTH_SESSION_CONTINUITY_EXPIRED'}),
          401,
        );
      });
      final coordinator = SessionRenewalCoordinator(
        config: config,
        client: inner,
        credentialStore: store,
        now: () => now,
      );
      final repository = HttpDecisionRepository(
        config: config,
        client: inner,
        credentialStore: store,
        sessionRenewalCoordinator: coordinator,
      );

      await expectLater(
        repository.ensureGuestCredential(),
        throwsA(
          isA<ApiFailure>().having(
            (error) => error.code,
            'code',
            'AUTH_GUEST_CONTINUITY_REQUIRED',
          ),
        ),
      );
    },
  );
}

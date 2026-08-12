import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/storage/credential_bundle.dart';

void main() {
  test('credential bundle round-trips exact server lifecycle metadata', () {
    final expiresAt = DateTime.utc(2026, 9, 11, 12, 30);
    final bundle = SessionCredentialBundle(
      actorId: 'actor-123',
      actorKind: 'GUEST',
      accessToken: 'kefe_g_access',
      accessExpiresAt: expiresAt,
      renewalToken: 'kefe_r_renewal',
      rotationCounter: 7,
    );

    final decoded = SessionCredentialBundle.decode(bundle.encode());

    expect(decoded, isNotNull);
    expect(decoded!.actorId, bundle.actorId);
    expect(decoded.actorKind, bundle.actorKind);
    expect(decoded.accessToken, bundle.accessToken);
    expect(decoded.accessExpiresAt, expiresAt);
    expect(decoded.renewalToken, bundle.renewalToken);
    expect(decoded.rotationCounter, 7);
  });

  test('credential bundle rejects unsupported versions', () {
    const raw = '{"version":1,"actor_id":"legacy"}';
    expect(SessionCredentialBundle.decode(raw), isNull);
  });
}

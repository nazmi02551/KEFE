import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'credential_bundle.dart';
import 'session_credential_store.dart';

class SecureCredentialStore implements SessionCredentialStore {
  SecureCredentialStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'kefe.guest.access_token.v1';
  static const _actorIdKey = 'kefe.actor_id.v1';
  static const _bundleKey = 'kefe.session.credential_bundle.v2';

  final FlutterSecureStorage _storage;

  @override
  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _actorIdKey),
      _storage.delete(key: _bundleKey),
    ]);
  }

  @override
  Future<String?> read() async {
    final bundle = await readBundle();
    if (bundle != null) return bundle.accessToken;
    return _storage.read(key: _accessTokenKey);
  }

  @override
  Future<String?> readActorId() async {
    final bundle = await readBundle();
    if (bundle != null) return bundle.actorId;
    return _storage.read(key: _actorIdKey);
  }

  @override
  Future<void> write(String token) =>
      _storage.write(key: _accessTokenKey, value: token);

  @override
  Future<void> writeActorId(String actorId) =>
      _storage.write(key: _actorIdKey, value: actorId);

  @override
  Future<SessionCredentialBundle?> readBundle() async {
    final raw = await _storage.read(key: _bundleKey);
    return SessionCredentialBundle.decode(raw);
  }

  @override
  Future<void> writeBundle(SessionCredentialBundle bundle) async {
    await _storage.write(key: _bundleKey, value: bundle.encode());
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _actorIdKey),
    ]);
  }

  @override
  Future<void> clearBundle() => _storage.delete(key: _bundleKey);
}

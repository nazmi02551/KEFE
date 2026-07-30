import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../features/decision/data/http_decision_repository.dart';

class SecureCredentialStore implements CredentialStore {
  SecureCredentialStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'kefe.guest.access_token.v1';

  final FlutterSecureStorage _storage;

  @override
  Future<void> clear() => _storage.delete(key: _accessTokenKey);

  @override
  Future<String?> read() => _storage.read(key: _accessTokenKey);

  @override
  Future<void> write(String token) =>
      _storage.write(key: _accessTokenKey, value: token);
}

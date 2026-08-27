import 'dart:convert';

class SessionCredentialBundle {
  const SessionCredentialBundle({
    required this.actorId,
    required this.actorKind,
    required this.accessToken,
    required this.accessExpiresAt,
    required this.renewalToken,
    required this.rotationCounter,
  });

  static const version = 2;

  final String actorId;
  final String actorKind;
  final String accessToken;
  final DateTime accessExpiresAt;
  final String renewalToken;
  final int rotationCounter;

  String encode() => jsonEncode(<String, Object>{
    'version': version,
    'actor_id': actorId,
    'actor_kind': actorKind,
    'access_token': accessToken,
    'access_expires_at': accessExpiresAt.toUtc().toIso8601String(),
    'renewal_token': renewalToken,
    'rotation_counter': rotationCounter,
  });

  static SessionCredentialBundle? decode(String? raw) {
    if (raw == null || raw.isEmpty) return null;
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, Object?> || decoded['version'] != version) {
      return null;
    }
    final actorId = decoded['actor_id'];
    final actorKind = decoded['actor_kind'];
    final accessToken = decoded['access_token'];
    final accessExpiresAt = decoded['access_expires_at'];
    final renewalToken = decoded['renewal_token'];
    final rotationCounter = decoded['rotation_counter'];
    if (actorId is! String ||
        actorKind is! String ||
        accessToken is! String ||
        accessExpiresAt is! String ||
        renewalToken is! String ||
        rotationCounter is! int) {
      return null;
    }
    return SessionCredentialBundle(
      actorId: actorId,
      actorKind: actorKind,
      accessToken: accessToken,
      accessExpiresAt: DateTime.parse(accessExpiresAt).toUtc(),
      renewalToken: renewalToken,
      rotationCounter: rotationCounter,
    );
  }
}

abstract interface class AtomicCredentialBundleStore {
  Future<SessionCredentialBundle?> readBundle();
  Future<void> writeBundle(SessionCredentialBundle bundle);
  Future<void> clearBundle();
}

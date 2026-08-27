import 'credential_bundle.dart';

abstract interface class SessionCredentialStore
    implements AtomicCredentialBundleStore {
  Future<String?> read();
  Future<String?> readActorId();
  Future<void> write(String token);
  Future<void> writeActorId(String actorId);
  Future<void> clear();
}

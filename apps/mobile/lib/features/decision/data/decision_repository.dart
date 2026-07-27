import '../domain/decision_models.dart';

abstract interface class DecisionRepository {
  Future<GuestCredential> ensureGuestCredential();

  Future<DecisionCase> fetchCase(String caseId);

  Future<String> startSession(String caseId);

  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  });

  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  });

  Future<RevealResult> reveal(String sessionId);
}

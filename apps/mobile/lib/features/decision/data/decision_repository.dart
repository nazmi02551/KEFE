import '../domain/decision_models.dart';

class ClientTransportFailure implements Exception {
  const ClientTransportFailure({this.code = 'NETWORK_UNAVAILABLE'});

  final String code;

  @override
  String toString() => 'ClientTransportFailure($code)';
}

abstract interface class DecisionRepository {
  Future<GuestCredential> ensureGuestCredential();

  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20});

  Future<DecisionCase> fetchCase(String caseId);

  Future<String> startSession(String caseId);

  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  });

  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  });

  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  });

  Future<RevealResult> reveal(String sessionId);
}

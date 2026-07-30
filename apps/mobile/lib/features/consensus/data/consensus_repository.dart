import '../domain/consensus_models.dart';

abstract interface class ConsensusRepository {
  Future<List<ConsensusCard>> fetchCards({
    required String sessionId,
    required String caseVersionId,
  });

  Future<ConsensusCard> participate({
    required String sessionId,
    required String caseVersionId,
    required String cardId,
    required String cardVersionId,
    required String stanceCode,
    required List<String> reasonTagCodes,
    required String idempotencyKey,
  });
}

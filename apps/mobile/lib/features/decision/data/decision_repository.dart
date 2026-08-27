import '../domain/decision_models.dart';
import '../domain/reflection_models.dart';

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

abstract interface class FlowRuntimeRepository {
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId);
}

abstract interface class PublicCaseHistoryRepository {
  Future<List<PublicCaseVersion>> fetchPublicCaseHistory(String caseId);
}

extension PublicCaseHistoryRepositoryAccess on DecisionRepository {
  Future<List<PublicCaseVersion>> fetchPublicCaseHistory(String caseId) {
    final repository = this;
    if (repository is PublicCaseHistoryRepository) {
      return repository.fetchPublicCaseHistory(caseId);
    }
    throw const ClientTransportFailure(
      code: 'PUBLIC_CASE_HISTORY_NOT_CONFIGURED',
    );
  }
}

abstract interface class DecisionLineageRepository {
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  });

  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  });

  Future<void> saveRevisionReason({
    required String sessionId,
    required String stepCode,
    required List<String> tags,
    required String? text,
  });

  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  });
}

abstract interface class ReflectionRepository {
  Future<ReflectionReadModel> fetchReflection({
    required String sessionId,
    required String stepCode,
  });

  Future<void> completeReflection({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  });
}

extension FlowRuntimeRepositoryAccess on DecisionRepository {
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) {
    final repository = this;
    if (repository is FlowRuntimeRepository) {
      return (repository as FlowRuntimeRepository).fetchFlowRuntime(sessionId);
    }
    throw const ClientTransportFailure(code: 'FLOW_RUNTIME_NOT_CONFIGURED');
  }
}

extension DecisionLineageRepositoryAccess on DecisionRepository {
  DecisionLineageRepository get lineage {
    final repository = this;
    if (repository is DecisionLineageRepository) {
      return repository as DecisionLineageRepository;
    }
    throw const ClientTransportFailure(code: 'DECISION_LINEAGE_NOT_CONFIGURED');
  }
}

extension ReflectionRepositoryAccess on DecisionRepository {
  ReflectionRepository get reflection {
    final repository = this;
    if (repository is ReflectionRepository) {
      return repository as ReflectionRepository;
    }
    throw const ClientTransportFailure(code: 'REFLECTION_NOT_CONFIGURED');
  }
}

abstract interface class PerspectiveRepository {
  Future<PerspectiveResult> fetchPerspectives(String sessionId);
}

extension PerspectiveRepositoryAccess on DecisionRepository {
  Future<PerspectiveResult> fetchPerspectives(String sessionId) {
    final repository = this;
    if (repository is PerspectiveRepository) {
      return (repository as PerspectiveRepository).fetchPerspectives(sessionId);
    }
    throw const ClientTransportFailure(code: 'PERSPECTIVE_NOT_CONFIGURED');
  }
}

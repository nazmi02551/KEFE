import '../../decision/data/decision_repository.dart';
import '../domain/context_models.dart';

abstract interface class ContextRepository {
  Future<CaseContextSnapshot> fetchContext(String caseVersionId);
}

extension ContextRepositoryAccess on DecisionRepository {
  Future<CaseContextSnapshot> fetchContext(String caseVersionId) {
    final repository = this;
    if (repository is ContextRepository) {
      return (repository as ContextRepository).fetchContext(caseVersionId);
    }
    throw const ClientTransportFailure(code: 'CONTEXT_NOT_CONFIGURED');
  }
}

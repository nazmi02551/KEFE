import '../domain/case_media_models.dart';

abstract interface class CaseMediaRepository {
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  });
}

class EmptyCaseMediaRepository implements CaseMediaRepository {
  const EmptyCaseMediaRepository();

  @override
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  }) async {
    return const [];
  }
}

import '../../context/domain/context_models.dart';
import '../domain/decision_models.dart';
import '../domain/reflection_models.dart';
import 'decision_repository.dart';
import 'preview_decision_repository.dart';

/// Product Preview repository that adds one explicit multi-stage DecisionRevision
/// journey on top of the deterministic preview catalog.
///
/// The base preview repository remains the simple Commit -> Reveal fixture used by
/// production-like UI tests. This subclass is only wired from `main_preview.dart`
/// and Product Preview tests.
class PreviewJourneyDecisionRepository extends PreviewDecisionRepository
    implements ReflectionRepository {
  static const journeyCaseId = '11111111-1111-4111-8111-111111111116';
  static const journeyCaseVersionId = '22222222-2222-4222-8222-222222222227';

  final Map<String, String> _sessionCaseIds = <String, String>{};
  final Map<String, _PreviewJourneyState> _journeys =
      <String, _PreviewJourneyState>{};

  @override
  Future<String> startSession(String requestedCaseId) async {
    final sessionId = await super.startSession(requestedCaseId);
    _sessionCaseIds[sessionId] = requestedCaseId;
    if (requestedCaseId == journeyCaseId) {
      _journeys[sessionId] = _PreviewJourneyState();
    }
    return sessionId;
  }

  bool _isJourney(String sessionId) =>
      _sessionCaseIds[sessionId] == journeyCaseId;

  _PreviewJourneyState _journey(String sessionId) =>
      _journeys.putIfAbsent(sessionId, _PreviewJourneyState.new);

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    if (!_isJourney(sessionId)) {
      return super.fetchFlowRuntime(sessionId);
    }

    final journey = _journey(sessionId);
    return FlowRuntimeSnapshot(
      sessionId: sessionId,
      caseVersionId: journeyCaseVersionId,
      sessionState: journey.initialCommitted ? 'COMMITTED' : 'DRAFT',
      templateCode: 'PRINCIPLE_CONTEXT_RETEST',
      templateVersionNo: 1,
      entryStepCode: 'PRINCIPLE',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        FlowRuntimeStep(
          code: 'PRINCIPLE',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['PRINCIPLE_FIRST'],
          nextStepCodes: const ['COUNTERVIEW_CONTEXT'],
          state: journey.initialCommitted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'COUNTERVIEW_CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: const ['COUNTERARGUMENT'],
          nextStepCodes: const ['FINAL_DECISION'],
          state: !journey.initialCommitted
              ? FlowStepRuntimeState.blocked
              : journey.contextExposed
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !journey.initialCommitted
              ? 'FLOW_PREDECESSOR_PENDING'
              : null,
        ),
        FlowRuntimeStep(
          code: 'FINAL_DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['COMMIT_FIRST', 'DECISION_REVISION'],
          nextStepCodes: const ['REFLECTION'],
          state: !journey.contextExposed
              ? FlowStepRuntimeState.blocked
              : journey.finalCommitted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !journey.contextExposed
              ? 'FLOW_PREDECESSOR_PENDING'
              : null,
        ),
        FlowRuntimeStep(
          code: 'REFLECTION',
          primitiveCode: 'REFLECTION',
          capabilityCodes: const ['REFLECTION'],
          nextStepCodes: const [],
          state: !journey.finalCommitted
              ? FlowStepRuntimeState.blocked
              : journey.reflectionCompleted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !journey.finalCommitted
              ? 'FLOW_PREDECESSOR_PENDING'
              : null,
        ),
      ],
    );
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {
    if (_isJourney(sessionId)) {
      _journey(sessionId).initialResponses[questionId] = value;
    }
    await super.answer(
      sessionId: sessionId,
      questionId: questionId,
      value: value,
    );
  }

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    if (_isJourney(sessionId)) {
      _journey(sessionId).initialCommitted = true;
    }
    await super.commit(sessionId: sessionId, idempotencyKey: idempotencyKey);
  }

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    if (_isJourney(sessionId) && stepCode == 'COUNTERVIEW_CONTEXT') {
      _journey(sessionId).contextExposed = true;
      return;
    }
    await super.recordFlowStepExposure(
      sessionId: sessionId,
      stepCode: stepCode,
      idempotencyKey: idempotencyKey,
    );
  }

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) async {
    if (_isJourney(sessionId) && stepCode == 'FINAL_DECISION') {
      _journey(sessionId).finalResponses[questionId] = value;
      return;
    }
    await super.answerRevision(
      sessionId: sessionId,
      stepCode: stepCode,
      questionId: questionId,
      value: value,
    );
  }

  @override
  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    if (_isJourney(sessionId) && stepCode == 'FINAL_DECISION') {
      _journey(sessionId).finalCommitted = true;
    }
    await super.commitRevision(
      sessionId: sessionId,
      stepCode: stepCode,
      idempotencyKey: idempotencyKey,
    );
  }

  @override
  Future<ReflectionReadModel> fetchReflection({
    required String sessionId,
    required String stepCode,
  }) async {
    if (!_isJourney(sessionId) || stepCode != 'REFLECTION') {
      throw const ClientTransportFailure(code: 'REFLECTION_NOT_AVAILABLE');
    }

    final journey = _journey(sessionId);
    final questionIds = <String>{
      ...journey.initialResponses.keys,
      ...journey.finalResponses.keys,
    };
    final changedCount = questionIds
        .where(
          (questionId) =>
              journey.initialResponses[questionId] !=
              journey.finalResponses[questionId],
        )
        .length;

    return ReflectionReadModel(
      sessionId: sessionId,
      caseVersionId: journeyCaseVersionId,
      flowStepCode: stepCode,
      revisionCount: 2,
      latestRevisionId: 'preview-revision-2-$sessionId',
      latestDeltaId: 'preview-delta-1-$sessionId',
      decisionChanged: changedCount > 0,
      changedQuestionCount: changedCount,
      interventionCount: journey.contextExposed ? 1 : 0,
      interventionTypeCodes: journey.contextExposed
          ? const ['CONTEXT_REVEAL']
          : const [],
      fromContributionClass: 'CORE_PRE_RESULT',
      toContributionClass: 'CORE_PRE_RESULT',
      completed: journey.reflectionCompleted,
    );
  }

  @override
  Future<void> completeReflection({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    if (!_isJourney(sessionId) || stepCode != 'REFLECTION') {
      throw const ClientTransportFailure(code: 'REFLECTION_NOT_AVAILABLE');
    }
    _journey(sessionId).reflectionCompleted = true;
  }

  @override
  Future<CaseContextSnapshot> fetchContext(
    String requestedCaseVersionId,
  ) async {
    if (requestedCaseVersionId != journeyCaseVersionId) {
      return super.fetchContext(requestedCaseVersionId);
    }

    const sourceId = 'preview-journey-counterview-source';
    return CaseContextSnapshot(
      caseVersionId: journeyCaseVersionId,
      sources: [
        CaseContextSource(
          id: sourceId,
          title: 'KEFE Product Preview · karşı görüş senaryosu',
          publisher: 'KEFE Editoryal',
          sourceKind: 'EDITORIAL',
          url: null,
          publishedAt: DateTime.utc(2026, 7, 29),
        ),
      ],
      blocks: const [
        CaseContextBlock(
          id: 'preview-journey-counterview',
          displayOrder: 1,
          disclosureLevel: 'ESSENTIAL',
          title: 'Karşı görüş',
          body:
              'Ücretsiz yan yana oturma zorunluluğuna karşı görüş; koltuk envanterinin son anda değişebildiğini, farklı ücret sınıflarının aynı uçuşta birlikte yönetildiğini ve katı bir garantinin diğer yolcuların koltuk seçimlerini de etkileyebileceğini savunuyor.',
          claimStatus: 'CLAIMED',
          sourceIds: [sourceId],
        ),
        CaseContextBlock(
          id: 'preview-journey-retest-note',
          displayOrder: 2,
          disclosureLevel: 'ESSENTIAL',
          title: 'Şimdi yeniden tart',
          body:
              'Bu karşı görüşü görmek ilk kararını otomatik olarak doğru ya da yanlış yapmaz. Aynı soruyu ikinci kez tart; KEFE yalnızca iki karar arasındaki gözlenen farkı kaydeder.',
          claimStatus: 'VERIFIED',
          sourceIds: [sourceId],
        ),
        CaseContextBlock(
          id: 'preview-journey-disclosure',
          displayOrder: 3,
          disclosureLevel: 'DETAIL',
          title: 'Preview notu',
          body:
              'Bu karşı görüş ve yolculuk temsili Product Preview verisidir. Canlı kullanıcı veya araştırma sonucu değildir.',
          claimStatus: 'VERIFIED',
          sourceIds: [sourceId],
        ),
      ],
    );
  }
}

class _PreviewJourneyState {
  bool initialCommitted = false;
  bool contextExposed = false;
  bool finalCommitted = false;
  bool reflectionCompleted = false;
  final Map<String, Object?> initialResponses = <String, Object?>{};
  final Map<String, Object?> finalResponses = <String, Object?>{};
}

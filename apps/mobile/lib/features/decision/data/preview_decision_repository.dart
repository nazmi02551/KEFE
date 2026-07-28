import '../domain/decision_models.dart';
import 'decision_repository.dart';

class PreviewDecisionRepository
    implements DecisionRepository, FlowRuntimeRepository, PerspectiveRepository {
  static const caseId = '11111111-1111-4111-8111-111111111111';
  static const caseVersionId = '22222222-2222-4222-8222-222222222222';

  bool _committed = false;
  String _sessionId = 'preview-session';

  static const _case = DecisionCase(
    id: caseId,
    versionId: caseVersionId,
    title: 'Son koltuk kime verilmeli?',
    summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı tart.',
    format: 'DILEMMA',
    domain: 'DAILY_LIFE',
    risk: 'L0',
    questions: [
      DecisionQuestion(
        id: '33333333-3333-4333-8333-333333333333',
        prompt: 'Son koltuğu kime verirdin?',
        responseType: 'SINGLE_CHOICE',
        options: ['A', 'B'],
        responseSchema: {
          'options': ['A', 'B'],
          'reason': {
            'tags': ['FAIRNESS', 'NEED', 'RESPONSIBILITY', 'PRACTICAL_IMPACT'],
            'max_tags': 3,
            'text_enabled': true,
            'text_max_length': 500,
          },
        },
      ),
      DecisionQuestion(
        id: '77777777-7777-4777-8777-777777777777',
        prompt: 'Bu kararından ne kadar eminsin?',
        responseType: 'CONFIDENCE',
        required: false,
        responseSchema: {'min': 1, 'max': 5, 'step': 1},
      ),
    ],
  );

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
    actorId: 'preview-actor',
    accessToken: 'preview-token',
    expiresAt: DateTime.utc(2030),
  );

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [
        DecisionCaseSummary(
          id: caseId,
          versionId: caseVersionId,
          title: 'Son koltuk kime verilmeli?',
          summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı tart.',
          format: 'DILEMMA',
          domain: 'DAILY_LIFE',
          risk: 'L0',
        ),
      ];

  @override
  Future<DecisionCase> fetchCase(String requestedCaseId) async => _case;

  @override
  Future<String> startSession(String requestedCaseId) async {
    _committed = false;
    _sessionId = 'preview-session';
    return _sessionId;
  }

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    return FlowRuntimeSnapshot(
      sessionId: _sessionId,
      caseVersionId: caseVersionId,
      sessionState: _committed ? 'COMMITTED' : 'DRAFT',
      templateCode: 'STANDARD_COMMIT_REVEAL',
      templateVersionNo: 1,
      entryStepCode: 'CONTEXT',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        const FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: ['SOURCE_REVEAL'],
          nextStepCodes: ['DECISION'],
          state: FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['COMMIT_FIRST', 'CONFIDENCE_CAPTURE'],
          nextStepCodes: const ['RESULT'],
          state: _committed
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'RESULT',
          primitiveCode: 'COLLECTIVE_RESULT',
          capabilityCodes: const [],
          nextStepCodes: const [],
          state: _committed
              ? FlowStepRuntimeState.ready
              : FlowStepRuntimeState.blocked,
          reasonCode: _committed ? null : 'FLOW_COMMIT_REQUIRED',
        ),
      ],
    );
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    _committed = true;
  }

  @override
  Future<RevealResult> reveal(String sessionId) async => const RevealResult(
    layer: 'TRUSTED',
    sampleSize: 1284,
    confidence: 'HIGH',
    values: {'A': 0.57, 'B': 0.43},
  );

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) async {
    return PerspectiveResult(
      sessionId: _sessionId,
      caseVersionId: caseVersionId,
      cards: const [
        PerspectiveCard(
          id: 'preview-near',
          slot: PerspectiveSlot.near,
          body: 'İhtiyacı daha acil görünen kişiye öncelik vermek zararı azaltabilir.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE editoryal',
          moderationState: 'NOT_REQUIRED',
        ),
        PerspectiveCard(
          id: 'preview-opposing',
          slot: PerspectiveSlot.opposing,
          body: 'Sırayı korumak, kişisel değerlendirmeden doğacak keyfiliği sınırlayabilir.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE editoryal',
          moderationState: 'NOT_REQUIRED',
        ),
        PerspectiveCard(
          id: 'preview-bridge',
          slot: PerspectiveSlot.bridge,
          body: 'Acil ihtiyacı gözetirken sırada bekleyenin hakkını açık bir ölçütle korumak iki kaygıyı birlikte taşıyabilir.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE editoryal',
          moderationState: 'NOT_REQUIRED',
        ),
      ],
      methodology: PerspectiveMethodology(
        mode: 'DEGRADED_CURATED',
        sampleKind: 'CURATED_FALLBACK',
        sampleSize: 3,
        generatedAt: DateTime.utc(2026, 7, 28),
        provenanceNote: 'Preview build için sabit, editoryal demo perspektifleri.',
      ),
    );
  }
}

import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

FlowRuntimeSnapshot standardFlowRuntime({
  String sessionId = 'session-1',
  String caseVersionId = 'version-1',
  bool committed = false,
}) {
  return FlowRuntimeSnapshot(
    sessionId: sessionId,
    caseVersionId: caseVersionId,
    sessionState: committed ? 'COMMITTED' : 'DRAFT',
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
        capabilityCodes: const ['COMMIT_FIRST'],
        nextStepCodes: const ['RESULT'],
        state: committed
            ? FlowStepRuntimeState.completed
            : FlowStepRuntimeState.ready,
      ),
      FlowRuntimeStep(
        code: 'RESULT',
        primitiveCode: 'COLLECTIVE_RESULT',
        capabilityCodes: const [],
        nextStepCodes: const [],
        state: committed
            ? FlowStepRuntimeState.ready
            : FlowStepRuntimeState.blocked,
        reasonCode: committed ? null : 'FLOW_COMMIT_REQUIRED',
      ),
    ],
  );
}

mixin StandardFlowRuntimeFake
    implements FlowRuntimeRepository, DecisionLineageRepository {
  bool flowCommitted = false;
  String flowSessionId = 'session-1';
  String flowCaseVersionId = 'version-1';

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    flowSessionId = sessionId;
    return standardFlowRuntime(
      sessionId: sessionId,
      caseVersionId: flowCaseVersionId,
      committed: flowCommitted,
    );
  }

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {}

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> saveRevisionReason({
    required String sessionId,
    required String stepCode,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {}
}

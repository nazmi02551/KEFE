import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/domain/decision_draft.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

void main() {
  test('DecisionDraft round-trips the session-pinned Flow snapshot', () {
    const caseData = DecisionCase(
      id: 'case-1',
      versionId: 'version-1',
      title: 'Fixture',
      summary: 'Flow persistence fixture',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [],
    );
    const flow = FlowRuntimeSnapshot(
      sessionId: 'session-1',
      caseVersionId: 'version-1',
      sessionState: 'DRAFT',
      templateCode: 'STANDARD_COMMIT_REVEAL',
      templateVersionNo: 1,
      entryStepCode: 'CONTEXT',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: ['SOURCE_REVEAL'],
          nextStepCodes: ['DECISION'],
          state: FlowStepRuntimeState.ready,
        ),
      ],
    );
    final draft = DecisionDraft(
      caseData: caseData,
      sessionId: 'session-1',
      flowRuntime: flow,
      responses: const {'q1': 'A'},
      updatedAt: DateTime.utc(2026, 7, 28),
    );

    final restored = DecisionDraft.fromJson(draft.toJson());

    expect(restored.flowRuntime, isNotNull);
    expect(restored.flowRuntime!.sessionId, 'session-1');
    expect(restored.flowRuntime!.caseVersionId, 'version-1');
    expect(restored.flowRuntime!.templateCode, 'STANDARD_COMMIT_REVEAL');
    expect(restored.flowRuntime!.steps.single.primitiveCode, 'CONTEXT');
    expect(restored.effectiveResponses, {'q1': 'A'});
  });

  test('legacy DecisionDraft without Flow remains readable but has no Flow authority', () {
    final restored = DecisionDraft.fromJson({
      'case': {
        'id': 'case-1',
        'version_id': 'version-1',
        'title': 'Legacy fixture',
        'summary': 'Legacy draft',
        'format': 'DILEMMA',
        'domain': 'DAILY_LIFE',
        'risk': 'L0',
        'questions': <Object?>[],
      },
      'session_id': 'legacy-session',
      'responses': {'q1': 'B'},
      'reason_tags': <Object?>[],
      'phase': 'editing',
      'updated_at': DateTime.utc(2026, 7, 27).toIso8601String(),
    });

    expect(restored.flowRuntime, isNull);
    expect(restored.effectiveResponses, {'q1': 'B'});
  });
}

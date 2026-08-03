import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/decision_journey_stage_resolver.dart';

FlowRuntimeStep step(String code, FlowStepRuntimeState state) =>
    FlowRuntimeStep(
      code: code,
      primitiveCode: code.toUpperCase(),
      capabilityCodes: const [],
      nextStepCodes: const [],
      state: state,
    );

FlowRuntimeSnapshot runtime(List<FlowRuntimeStep> steps) => FlowRuntimeSnapshot(
  sessionId: 'session-1',
  caseVersionId: 'version-1',
  sessionState: 'ACTIVE',
  templateCode: 'TEST',
  templateVersionNo: 1,
  entryStepCode: steps.first.code,
  executionSupport: FlowExecutionSupport.full,
  steps: steps,
);

void main() {
  test('prefers the furthest runtime-ready step', () {
    final snapshot = runtime([
      step('context', FlowStepRuntimeState.ready),
      step('decision', FlowStepRuntimeState.ready),
      step('result', FlowStepRuntimeState.blocked),
    ]);

    expect(DecisionJourneyStageResolver.primary(snapshot)?.code, 'decision');
    expect(
      DecisionJourneyStageResolver.ordinal(
        snapshot,
        DecisionJourneyStageResolver.primary(snapshot)!,
      ),
      2,
    );
  });

  test('uses unsupported only when no ready step exists', () {
    final snapshot = runtime([
      step('context', FlowStepRuntimeState.completed),
      step('revision', FlowStepRuntimeState.unsupported),
      step('reflection', FlowStepRuntimeState.blocked),
    ]);

    expect(DecisionJourneyStageResolver.primary(snapshot)?.code, 'revision');
  });

  test('falls back to the final completed step for terminal journeys', () {
    final snapshot = runtime([
      step('context', FlowStepRuntimeState.completed),
      step('decision', FlowStepRuntimeState.completed),
    ]);

    expect(DecisionJourneyStageResolver.primary(snapshot)?.code, 'decision');
  });

  test('does not invent a stage for an empty runtime', () {
    final snapshot = FlowRuntimeSnapshot(
      sessionId: 'session-1',
      caseVersionId: 'version-1',
      sessionState: 'ACTIVE',
      templateCode: 'EMPTY',
      templateVersionNo: 1,
      entryStepCode: '',
      executionSupport: FlowExecutionSupport.partial,
      steps: const [],
    );

    expect(DecisionJourneyStageResolver.primary(snapshot), isNull);
  });
}

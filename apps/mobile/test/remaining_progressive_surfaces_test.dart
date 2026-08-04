import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/decision_journey_stage_resolver.dart';
import 'package:kefe_mobile/features/decision/presentation/post_commit_journey.dart';

void main() {
  test('remaining progressive surfaces contract closes intended scope', () {
    final file = File(
      '../../docs/contracts/progressive-result-context-history.v1.json',
    );
    expect(file.existsSync(), isTrue);
    final contract =
        jsonDecode(file.readAsStringSync()) as Map<String, Object?>;
    final postCommit = contract['post_commit']! as Map<String, Object?>;
    final context = contract['context']! as Map<String, Object?>;
    final myKefe = contract['my_kefe']! as Map<String, Object?>;

    expect(postCommit['authoritative_primitive'], 'COLLECTIVE_RESULT');
    expect(postCommit['presentation_only'], isTrue);
    expect(context['continue_requires_optional_layers'], isFalse);
    expect(context['legacy_default_unchanged'], isTrue);
    expect(myKefe['whole_screen_wizard'], isFalse);
    expect(myKefe['recent_journey_expandable'], isTrue);
  });

  test('post-Commit journey has stable generic stage order', () {
    expect(
      PostCommitJourneyResolver.stages.map((stage) => stage.kind).toList(),
      const [
        PostCommitJourneyStageKind.result,
        PostCommitJourneyStageKind.perspectives,
        PostCommitJourneyStageKind.participation,
        PostCommitJourneyStageKind.completion,
      ],
    );
    expect(PostCommitJourneyResolver.clampIndex(-1), 0);
    expect(PostCommitJourneyResolver.clampIndex(99), 3);
  });

  test('reweigh label detection follows pinned runtime order only', () {
    const first = FlowRuntimeStep(
      code: 'decision-1',
      primitiveCode: 'DECISION',
      capabilityCodes: [],
      nextStepCodes: ['context-2'],
      state: FlowStepRuntimeState.completed,
    );
    const second = FlowRuntimeStep(
      code: 'decision-2',
      primitiveCode: 'DECISION',
      capabilityCodes: [],
      nextStepCodes: ['reflection'],
      state: FlowStepRuntimeState.ready,
    );
    const runtime = FlowRuntimeSnapshot(
      sessionId: 'session',
      caseVersionId: 'version',
      sessionState: 'OPEN',
      templateCode: 'generic',
      templateVersionNo: 1,
      entryStepCode: 'decision-1',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        first,
        FlowRuntimeStep(
          code: 'context-2',
          primitiveCode: 'CONTEXT',
          capabilityCodes: [],
          nextStepCodes: ['decision-2'],
          state: FlowStepRuntimeState.completed,
        ),
        second,
      ],
    );

    expect(
      DecisionJourneyStageResolver.isRepeatedDecision(runtime, first),
      isFalse,
    );
    expect(
      DecisionJourneyStageResolver.isRepeatedDecision(runtime, second),
      isTrue,
    );
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

const partialCaseId = 'dddddddd-1111-4111-8111-dddddddddddd';

class PartialFlowRepository implements DecisionRepository, FlowRuntimeRepository {
  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {}

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'partial-actor',
      accessToken: 'partial-token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async {
    return const DecisionCase(
      id: partialCaseId,
      versionId: 'partial-version-1',
      title: 'Perspective retest fixture',
      summary: 'Aynı generic motorun henüz desteklenmeyen retest sınırı.',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: 'partial-question',
          prompt: 'İlk kararın nedir?',
          responseType: 'SINGLE_CHOICE',
          options: ['A', 'B'],
        ),
      ],
    );
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    return FlowRuntimeSnapshot(
      sessionId: sessionId,
      caseVersionId: 'partial-version-1',
      sessionState: 'COMMITTED',
      templateCode: 'PRINCIPLE_CONTEXT_RETEST',
      templateVersionNo: 1,
      entryStepCode: 'PRINCIPLE',
      executionSupport: FlowExecutionSupport.partial,
      steps: const [
        FlowRuntimeStep(
          code: 'PRINCIPLE',
          primitiveCode: 'DECISION',
          capabilityCodes: ['PRINCIPLE_FIRST'],
          nextStepCodes: ['CONTEXT'],
          state: FlowStepRuntimeState.completed,
        ),
        FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: ['COUNTERARGUMENT'],
          nextStepCodes: ['FINAL_DECISION'],
          state: FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'FINAL_DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: ['COMMIT_FIRST'],
          nextStepCodes: ['REFLECTION'],
          state: FlowStepRuntimeState.unsupported,
          reasonCode: 'FLOW_DECISION_REVISION_REQUIRED',
        ),
        FlowRuntimeStep(
          code: 'REFLECTION',
          primitiveCode: 'REFLECTION',
          capabilityCodes: ['REFLECTION'],
          nextStepCodes: [],
          state: FlowStepRuntimeState.blocked,
          reasonCode: 'FLOW_PREDECESSOR_PENDING',
        ),
      ],
    );
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 12,
      confidence: 'LOW',
      values: {'A': 0.5, 'B': 0.5},
    );
  }

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<String> startSession(String caseId) async => 'partial-session';
}

void main() {
  testWidgets('partial Flow exposes unsupported capability without fixed fallback', (
    tester,
  ) async {
    tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(PartialFlowRepository()),
          decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
        ],
        child: const KefeApp(initialLocation: '/case/$partialCaseId'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('capability-pending-FINAL_DECISION')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('commit-button')), findsNothing);
    expect(find.byKey(const ValueKey('option-A')), findsNothing);
  });
}

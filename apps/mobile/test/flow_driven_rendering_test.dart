import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/application/reflection_completion_provider.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/reflection_completion_store.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/domain/reflection_models.dart';

const retestCaseId = 'dddddddd-1111-4111-8111-dddddddddddd';

class RetestFlowRepository
    implements
        DecisionRepository,
        FlowRuntimeRepository,
        DecisionLineageRepository,
        ReflectionRepository {
  bool initialCommitted = false;
  bool contextExposed = false;
  bool finalCommitted = false;
  bool reflectionCompleted = false;
  int revealCalls = 0;
  int exposureCalls = 0;
  int revisionAnswerCalls = 0;
  int revisionCommitCalls = 0;
  int reflectionFetchCalls = 0;
  int reflectionCompleteCalls = 0;
  Object? finalAnswer;

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
  }) async {
    initialCommitted = true;
  }

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'retest-actor',
      accessToken: 'retest-token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async {
    return const DecisionCase(
      id: retestCaseId,
      versionId: 'retest-version-1',
      title: 'Perspective retest fixture',
      summary: 'Aynı generic motor Context sonrası kararı yeniden tartar.',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: 'retest-question',
          prompt: 'Kararın nedir?',
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
      caseVersionId: 'retest-version-1',
      sessionState: initialCommitted ? 'COMMITTED' : 'DRAFT',
      templateCode: 'PRINCIPLE_CONTEXT_RETEST',
      templateVersionNo: 1,
      entryStepCode: 'PRINCIPLE',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        FlowRuntimeStep(
          code: 'PRINCIPLE',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['PRINCIPLE_FIRST'],
          nextStepCodes: const ['CONTEXT'],
          state: initialCommitted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: const ['COUNTERARGUMENT'],
          nextStepCodes: const ['FINAL_DECISION'],
          state: !initialCommitted
              ? FlowStepRuntimeState.blocked
              : contextExposed
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !initialCommitted ? 'FLOW_PREDECESSOR_PENDING' : null,
        ),
        FlowRuntimeStep(
          code: 'FINAL_DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['COMMIT_FIRST'],
          nextStepCodes: const ['REFLECTION'],
          state: !contextExposed
              ? FlowStepRuntimeState.blocked
              : finalCommitted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !contextExposed ? 'FLOW_PREDECESSOR_PENDING' : null,
        ),
        FlowRuntimeStep(
          code: 'REFLECTION',
          primitiveCode: 'REFLECTION',
          capabilityCodes: const ['REFLECTION'],
          nextStepCodes: const [],
          state: !finalCommitted
              ? FlowStepRuntimeState.blocked
              : reflectionCompleted
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
          reasonCode: !finalCommitted ? 'FLOW_PREDECESSOR_PENDING' : null,
        ),
      ],
    );
  }

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    exposureCalls += 1;
    if (stepCode == 'CONTEXT') contextExposed = true;
  }

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) async {
    revisionAnswerCalls += 1;
    finalAnswer = value;
  }

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
  }) async {
    revisionCommitCalls += 1;
    finalCommitted = true;
  }

  @override
  Future<ReflectionReadModel> fetchReflection({
    required String sessionId,
    required String stepCode,
  }) async {
    reflectionFetchCalls += 1;
    return ReflectionReadModel(
      sessionId: sessionId,
      caseVersionId: 'retest-version-1',
      flowStepCode: stepCode,
      revisionCount: 2,
      latestRevisionId: 'revision-2',
      latestDeltaId: 'delta-1',
      decisionChanged: true,
      changedQuestionCount: 1,
      interventionCount: 1,
      interventionTypeCodes: const ['CONTEXT_REVEAL'],
      fromContributionClass: 'CORE_PRE_RESULT',
      toContributionClass: 'CORE_PRE_RESULT',
      completed: reflectionCompleted,
    );
  }

  @override
  Future<void> completeReflection({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    reflectionCompleteCalls += 1;
    reflectionCompleted = true;
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    revealCalls += 1;
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
  Future<String> startSession(String caseId) async => 'retest-session';
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    300,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pump();
  await tester.tap(finder);
  await tester.pump();
}

void main() {
  testWidgets('Flow UI executes DecisionRevision and Reflection generically', (
    tester,
  ) async {
    tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);
    final repository = RetestFlowRepository();
    final completionStore = MemoryReflectionCompletionStore();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(repository),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
          reflectionCompletionStoreProvider.overrideWithValue(completionStore),
        ],
        child: const KefeApp(initialLocation: '/case/$retestCaseId'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('option-A')), findsOneWidget);
    await tapVisible(tester, find.byKey(const ValueKey('option-A')));
    await tapVisible(tester, find.byKey(const ValueKey('commit-button')));
    await tester.pumpAndSettle();

    expect(repository.initialCommitted, isTrue);
    expect(repository.contextExposed, isTrue);
    expect(repository.revealCalls, 0);
    expect(find.byKey(const ValueKey('option-B')), findsOneWidget);

    await tapVisible(tester, find.byKey(const ValueKey('option-B')));
    await tapVisible(tester, find.byKey(const ValueKey('commit-button')));
    await tester.pumpAndSettle();

    expect(repository.revisionAnswerCalls, 1);
    expect(repository.finalAnswer, 'B');
    expect(repository.revisionCommitCalls, 1);
    expect(repository.finalCommitted, isTrue);
    expect(repository.revealCalls, 0);
    expect(
      find.byKey(const ValueKey('reflection-step-REFLECTION')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('reflection-summary')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('reflection-non-causal-note')),
      findsOneWidget,
    );
    expect(repository.reflectionFetchCalls, greaterThanOrEqualTo(1));

    await tapVisible(
      tester,
      find.byKey(const ValueKey('reflection-complete-button')),
    );
    await tester.pumpAndSettle();

    expect(repository.reflectionCompleteCalls, 1);
    expect(repository.reflectionCompleted, isTrue);
    expect(find.byKey(const ValueKey('reflection-completed')), findsOneWidget);
    expect(completionStore.completions, isEmpty);
    expect(repository.revealCalls, 0);
  });
}

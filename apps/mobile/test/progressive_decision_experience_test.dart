import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

const journeyCaseId = 'eeeeeeee-1111-4111-8111-eeeeeeeeeeee';

class ProgressiveJourneyRepository
    implements
        DecisionRepository,
        FlowRuntimeRepository,
        DecisionLineageRepository {
  bool contextExposed = false;
  int exposureCalls = 0;

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
    actorId: 'progressive-actor',
    accessToken: 'progressive-token',
    expiresAt: DateTime.utc(2026, 9),
  );

  @override
  Future<DecisionCase> fetchCase(String caseId) async => const DecisionCase(
    id: journeyCaseId,
    versionId: 'progressive-version-1',
    title: 'Aşamalı tartım testi',
    summary: 'Bağlam incelendikten sonra karar adımı açılır.',
    format: 'DILEMMA',
    domain: 'DAILY_LIFE',
    risk: 'L0',
    questions: [
      DecisionQuestion(
        id: 'progressive-question',
        prompt: 'Kararın nedir?',
        responseType: 'SINGLE_CHOICE',
        options: ['A', 'B'],
      ),
    ],
  );

  @override
  Future<String> startSession(String caseId) async => 'progressive-session';

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    return FlowRuntimeSnapshot(
      sessionId: sessionId,
      caseVersionId: 'progressive-version-1',
      sessionState: 'DRAFT',
      templateCode: 'CONTEXT_THEN_DECISION',
      templateVersionNo: 1,
      entryStepCode: 'CONTEXT',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: const ['SOURCE_REVEAL'],
          nextStepCodes: const ['DECISION'],
          state: contextExposed
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['COMMIT_FIRST'],
          nextStepCodes: const ['RESULT'],
          state: contextExposed
              ? FlowStepRuntimeState.ready
              : FlowStepRuntimeState.blocked,
          reasonCode: contextExposed ? null : 'FLOW_PREDECESSOR_PENDING',
        ),
        const FlowRuntimeStep(
          code: 'RESULT',
          primitiveCode: 'COLLECTIVE_RESULT',
          capabilityCodes: [],
          nextStepCodes: [],
          state: FlowStepRuntimeState.blocked,
          reasonCode: 'FLOW_COMMIT_REQUIRED',
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
    contextExposed = true;
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
  }) async {}

  @override
  Future<RevealResult> reveal(String sessionId) async => const RevealResult(
    layer: 'TRUSTED',
    sampleSize: 10,
    confidence: 'LOW',
    values: {'A': 0.5, 'B': 0.5},
  );

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];

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

Future<void> pumpCase(
  WidgetTester tester, {
  required ProgressiveJourneyRepository repository,
  required ExperiencePresentationConfig config,
}) async {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
        experiencePresentationConfigProvider.overrideWithValue(config),
      ],
      child: const KefeApp(initialLocation: '/case/$journeyCaseId'),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('progressive context advances only after explicit user action', (
    tester,
  ) async {
    final repository = ProgressiveJourneyRepository();
    await pumpCase(
      tester,
      repository: repository,
      config: const ExperiencePresentationConfig.progressive(),
    );

    expect(
      find.byKey(const ValueKey('progressive-decision-journey')),
      findsOneWidget,
    );
    expect(repository.contextExposed, isFalse);
    expect(find.byKey(const ValueKey('context-continue-button')), findsOneWidget);
    expect(find.byKey(const ValueKey('option-A')), findsNothing);

    final continueButton = find.byKey(
      const ValueKey('context-continue-button'),
    );
    await tester.ensureVisible(continueButton);
    await tester.tap(continueButton);
    await tester.pumpAndSettle();

    expect(repository.exposureCalls, 1);
    expect(repository.contextExposed, isTrue);
    expect(find.byKey(const ValueKey('option-A')), findsOneWidget);
    expect(find.byKey(const ValueKey('context-continue-button')), findsNothing);
  });

  testWidgets('legacy Decision renderer remains independently selectable', (
    tester,
  ) async {
    final repository = ProgressiveJourneyRepository();
    await pumpCase(
      tester,
      repository: repository,
      config: const ExperiencePresentationConfig.legacy(),
    );

    expect(
      find.byKey(const ValueKey('progressive-decision-journey')),
      findsNothing,
    );
    expect(repository.contextExposed, isTrue);
    expect(find.byKey(const ValueKey('option-A')), findsOneWidget);
  });
}

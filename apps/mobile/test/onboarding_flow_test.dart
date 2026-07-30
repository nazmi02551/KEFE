import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/onboarding/application/onboarding_controller.dart';
import 'package:kefe_mobile/features/onboarding/data/onboarding_store.dart';

import 'support/flow_runtime_fixture.dart';

const onboardingCaseId = '11111111-1111-4111-8111-111111111111';

class OnboardingFakeRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository {
  int exploreCalls = 0;
  int caseCalls = 0;
  int commitCalls = 0;

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
    commitCalls += 1;
    flowCommitted = true;
  }

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'actor-onboarding',
      accessToken: 'token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async {
    caseCalls += 1;
    return const DecisionCase(
      id: onboardingCaseId,
      versionId: 'version-1',
      title: 'Son koltuk kime verilmeli?',
      summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı tart.',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: 'question-1',
          prompt: 'Son koltuğu kime verirdin?',
          responseType: 'SINGLE_CHOICE',
          options: ['A', 'B'],
        ),
      ],
    );
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    exploreCalls += 1;
    return const [
      DecisionCaseSummary(
        id: onboardingCaseId,
        versionId: 'version-1',
        title: 'Son koltuk kime verilmeli?',
        summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı tart.',
        format: 'DILEMMA',
        domain: 'DAILY_LIFE',
        risk: 'L0',
      ),
    ];
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 1284,
      confidence: 'HIGH',
      values: {'A': 0.57, 'B': 0.43},
    );
  }

  @override
  Future<String> startSession(String caseId) async => 'session-onboarding';
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

Future<void> pumpOnboardingApp(
  WidgetTester tester, {
  required OnboardingFakeRepository repository,
  required MemoryOnboardingStore onboardingStore,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(
          MemoryDecisionDraftStore(),
        ),
        onboardingStoreProvider.overrideWithValue(onboardingStore),
      ],
      child: const KefeApp(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    300,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pump();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('fresh user sees two promises before the first real Case', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = OnboardingFakeRepository();
    final onboardingStore = MemoryOnboardingStore();

    await pumpOnboardingApp(
      tester,
      repository: repository,
      onboardingStore: onboardingStore,
    );

    expect(find.byKey(const ValueKey('onboarding-pages')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-1')), findsOneWidget);
    expect(repository.caseCalls, 0);

    await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('onboarding-promise-2')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(repository.caseCalls, 1);
  });

  testWidgets(
    'first Reveal persists onboarding completion before continuation',
    (tester) async {
      useTurkishLocale(tester);
      final repository = OnboardingFakeRepository();
      final onboardingStore = MemoryOnboardingStore();

      await pumpOnboardingApp(
        tester,
        repository: repository,
        onboardingStore: onboardingStore,
      );

      await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const ValueKey('option-A')));
      await tester.pump();
      await tapVisible(tester, find.byKey(const ValueKey('commit-button')));

      expect(repository.commitCalls, 1);
      expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
      expect(onboardingStore.completed, isTrue);

      final continueButton = find.byKey(const ValueKey('continue-as-guest'));
      await tester.scrollUntilVisible(
        continueButton,
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('first-use-completion')),
        findsOneWidget,
      );

      await tester.tap(continueButton);
      await tester.pumpAndSettle();

      expect(onboardingStore.completed, isTrue);
      expect(find.byKey(const ValueKey('explore-list')), findsOneWidget);
    },
  );

  testWidgets('completed user enters Explore without replaying onboarding', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = OnboardingFakeRepository();
    final onboardingStore = MemoryOnboardingStore()..completed = true;

    await pumpOnboardingApp(
      tester,
      repository: repository,
      onboardingStore: onboardingStore,
    );

    expect(find.byKey(const ValueKey('onboarding-pages')), findsNothing);
    expect(find.byKey(const ValueKey('explore-list')), findsOneWidget);
    expect(repository.exploreCalls, 1);
  });
}

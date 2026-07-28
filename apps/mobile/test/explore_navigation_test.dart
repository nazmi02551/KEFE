import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

import 'support/flow_runtime_fixture.dart';

const caseId = '11111111-1111-4111-8111-111111111111';

class ExploreFakeRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository {
  int fetchCaseCalls = 0;
  int startSessionCalls = 0;

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
    flowCommitted = true;
  }

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'actor-1',
      accessToken: 'token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String requestedCaseId) async {
    fetchCaseCalls += 1;
    expect(requestedCaseId, caseId);
    return const DecisionCase(
      id: caseId,
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
    return const [
      DecisionCaseSummary(
        id: caseId,
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
      sampleSize: 100,
      confidence: 'HIGH',
      values: {'A': 0.5, 'B': 0.5},
    );
  }

  @override
  Future<String> startSession(String requestedCaseId) async {
    startSessionCalls += 1;
    expect(requestedCaseId, caseId);
    return 'session-1';
  }
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

void main() {
  testWidgets('Explore opens a Case through the canonical deep-link route', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ExploreFakeRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(repository),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
        ],
        child: const KefeApp(initialLocation: '/explore'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('explore-list')), findsOneWidget);
    expect(find.byKey(const ValueKey('explore-case-$caseId')), findsOneWidget);
    expect(repository.fetchCaseCalls, 0);

    await tester.tap(find.byKey(const ValueKey('explore-case-$caseId')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(repository.fetchCaseCalls, 1);
    expect(repository.startSessionCalls, 1);
  });

  testWidgets('Case deep link bypasses Explore without breaking Commit First', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ExploreFakeRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(repository),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
        ],
        child: const KefeApp(initialLocation: '/case/$caseId'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });
}

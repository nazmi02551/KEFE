import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

class FakeDecisionRepository implements DecisionRepository {
  int commitCalls = 0;

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
    commitCalls += 1;
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
  Future<DecisionCase> fetchCase(String caseId) async {
    return const DecisionCase(
      id: demoCaseId,
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
  Future<RevealResult> reveal(String sessionId) async {
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 1284,
      confidence: 'HIGH',
      values: {'A': 0.57, 'B': 0.43},
    );
  }

  @override
  Future<String> startSession(String caseId) async => 'session-1';
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

void main() {
  testWidgets('Commit First hides result until a decision is committed', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [decisionRepositoryProvider.overrideWithValue(repository)],
        child: const KefeApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Topluluk nasıl tarttı?'), findsNothing);
    expect(find.text('Kararımı Ver'), findsOneWidget);

    await tester.tap(find.text('A'));
    await tester.pump();
    await tester.tap(find.text('Kararımı Ver'));
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 1);
    expect(find.text('Topluluk nasıl tarttı?'), findsOneWidget);
    expect(find.textContaining('n=1284'), findsOneWidget);
  });

  testWidgets('application supports dark theme without changing flow semantics', (
    tester,
  ) async {
    useTurkishLocale(tester);
    tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(FakeDecisionRepository()),
        ],
        child: const KefeApp(),
      ),
    );
    await tester.pumpAndSettle();

    final material = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(material.themeMode, ThemeMode.system);
    expect(find.text('Kararımı Ver'), findsOneWidget);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_draft.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

import 'support/flow_runtime_fixture.dart';

const sampleCase = DecisionCase(
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

const sampleSummary = DecisionCaseSummary(
  id: demoCaseId,
  versionId: 'version-1',
  title: 'Son koltuk kime verilmeli?',
  summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı tart.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
);

class FakeDecisionRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository {
  int answerCalls = 0;
  int commitCalls = 0;
  int revealCalls = 0;
  int startSessionCalls = 0;
  int commitTransportFailures = 0;
  int revealTransportFailures = 0;
  bool fetchCaseOffline = false;
  final List<String> commitKeys = [];

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {
    answerCalls += 1;
  }

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
    commitKeys.add(idempotencyKey);
    if (commitTransportFailures > 0) {
      commitTransportFailures -= 1;
      throw const ClientTransportFailure();
    }
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
  Future<DecisionCase> fetchCase(String caseId) async {
    if (fetchCaseOffline) {
      throw const ClientTransportFailure();
    }
    return sampleCase;
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    return const [sampleSummary];
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    revealCalls += 1;
    if (revealTransportFailures > 0) {
      revealTransportFailures -= 1;
      throw const ClientTransportFailure();
    }
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 1284,
      confidence: 'HIGH',
      values: {'A': 0.57, 'B': 0.43},
    );
  }

  @override
  Future<String> startSession(String caseId) async {
    startSessionCalls += 1;
    return 'session-1';
  }
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

Future<void> pumpKefe(
  WidgetTester tester,
  FakeDecisionRepository repository,
  MemoryDecisionDraftStore draftStore,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(draftStore),
      ],
      child: const KefeApp(initialLocation: '/case/$demoCaseId'),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> scrollTo(
  WidgetTester tester,
  Finder finder, {
  double delta = 260,
}) async {
  await tester.scrollUntilVisible(
    finder,
    delta,
    scrollable: find.byType(Scrollable).last,
  );
  await tester.pump();
}

void main() {
  testWidgets('Commit First hides result until a decision is committed', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository();
    final draftStore = MemoryDecisionDraftStore();
    await pumpKefe(tester, repository, draftStore);

    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);

    final option = find.byKey(const ValueKey('option-A'));
    await scrollTo(tester, option);
    await tester.tap(option);
    await tester.pump();

    final commit = find.byKey(const ValueKey('commit-button'));
    await scrollTo(tester, commit);
    await tester.tap(commit);
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 1);
    final reveal = find.byKey(const ValueKey('reveal-card'));
    await scrollTo(tester, reveal);
    expect(reveal, findsOneWidget);
    expect(find.byKey(const ValueKey('reveal-methodology')), findsOneWidget);
    expect(draftStore.draftFor(demoCaseId), isNull);
  });

  testWidgets('application supports dark theme without changing flow semantics', (
    tester,
  ) async {
    useTurkishLocale(tester);
    tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);

    await pumpKefe(
      tester,
      FakeDecisionRepository(),
      MemoryDecisionDraftStore(),
    );

    final material = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(material.themeMode, ThemeMode.system);
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });

  testWidgets('uncertain commit retries with the exact same idempotency key', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository()..commitTransportFailures = 1;
    final draftStore = MemoryDecisionDraftStore();
    await pumpKefe(tester, repository, draftStore);

    final option = find.byKey(const ValueKey('option-A'));
    await scrollTo(tester, option);
    await tester.tap(option);
    await tester.pump();

    final commit = find.byKey(const ValueKey('commit-button'));
    await scrollTo(tester, commit);
    await tester.tap(commit);
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 1);
    expect(
      draftStore.draftFor(demoCaseId)?.phase,
      DecisionDraftPhase.commitPending,
    );
    final status = find.byKey(const ValueKey('decision-status-message'));
    await scrollTo(tester, status);
    expect(status, findsOneWidget);

    final firstKey = repository.commitKeys.single;
    await scrollTo(tester, commit, delta: -260);
    await tester.tap(commit);
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 2);
    expect(repository.commitKeys, [firstKey, firstKey]);
    expect(repository.answerCalls, 1);
    final reveal = find.byKey(const ValueKey('reveal-card'));
    await scrollTo(tester, reveal);
    expect(reveal, findsOneWidget);
    expect(draftStore.draftFor(demoCaseId), isNull);
  });

  testWidgets('confirmed commit retries only Reveal after connectivity loss', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository()..revealTransportFailures = 1;
    final draftStore = MemoryDecisionDraftStore();
    await pumpKefe(tester, repository, draftStore);

    final option = find.byKey(const ValueKey('option-A'));
    await scrollTo(tester, option);
    await tester.tap(option);
    await tester.pump();

    final commit = find.byKey(const ValueKey('commit-button'));
    await scrollTo(tester, commit);
    await tester.tap(commit);
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 1);
    expect(repository.revealCalls, 1);
    expect(
      draftStore.draftFor(demoCaseId)?.phase,
      DecisionDraftPhase.committedAwaitingReveal,
    );

    await scrollTo(tester, commit);
    await tester.tap(commit);
    await tester.pumpAndSettle();

    expect(repository.commitCalls, 1);
    expect(repository.revealCalls, 2);
    final reveal = find.byKey(const ValueKey('reveal-card'));
    await scrollTo(tester, reveal);
    expect(reveal, findsOneWidget);
  });

  testWidgets('offline startup restores a cached pinned Flow draft', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository()..fetchCaseOffline = true;
    final draftStore = MemoryDecisionDraftStore();
    draftStore.drafts[demoCaseId] = DecisionDraft(
      caseData: sampleCase,
      sessionId: 'session-offline',
      flowRuntime: standardFlowRuntime(sessionId: 'session-offline'),
      questionId: 'question-1',
      selectedOption: 'B',
      updatedAt: DateTime.utc(2026, 7, 27),
    );

    await pumpKefe(tester, repository, draftStore);

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    final option = find.byKey(const ValueKey('option-B'));
    await scrollTo(tester, option);
    expect(option, findsOneWidget);
    final status = find.byKey(const ValueKey('decision-status-message'));
    await scrollTo(tester, status);
    expect(status, findsOneWidget);
    expect(repository.startSessionCalls, 0);
  });

  testWidgets('legacy offline draft never invents a default Flow', (tester) async {
    useTurkishLocale(tester);
    final repository = FakeDecisionRepository()..fetchCaseOffline = true;
    final draftStore = MemoryDecisionDraftStore();
    draftStore.drafts[demoCaseId] = DecisionDraft(
      caseData: sampleCase,
      sessionId: 'legacy-session',
      questionId: 'question-1',
      selectedOption: 'B',
      updatedAt: DateTime.utc(2026, 7, 27),
    );

    await pumpKefe(tester, repository, draftStore);

    expect(find.byKey(const ValueKey('error')), findsOneWidget);
    expect(find.byKey(const ValueKey('commit-button')), findsNothing);
  });
}

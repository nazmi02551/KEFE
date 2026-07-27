import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_draft.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

const reasonCaseId = 'bbbbbbbb-1111-4111-8111-bbbbbbbbbbbb';
const reasonQuestionId = 'reason-choice';

const reasonCase = DecisionCase(
  id: reasonCaseId,
  versionId: 'reason-version-1',
  title: 'Gerekçeni de tart',
  summary: 'Kararının arkasındaki nedeni yapılandırılmış biçimde kaydet.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: reasonQuestionId,
      prompt: 'Hangisini seçerdin?',
      responseType: 'SINGLE_CHOICE',
      options: ['A', 'B'],
      responseSchema: {
        'reason': {
          'tags': ['FAIRNESS', 'NEED', 'RESPONSIBILITY'],
          'max_tags': 2,
          'text_enabled': true,
          'text_max_length': 120,
        },
      },
    ),
  ],
);

class ReasonFakeRepository implements DecisionRepository {
  int answerCalls = 0;
  int reasonCalls = 0;
  int commitCalls = 0;
  int reasonTransportFailures = 0;
  int commitTransportFailures = 0;
  List<String> lastTags = const [];
  String? lastText;
  final List<String> commitKeys = [];
  final List<String> events = [];

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {
    answerCalls += 1;
    events.add('answer');
  }

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {
    reasonCalls += 1;
    events.add('reason');
    if (reasonTransportFailures > 0) {
      reasonTransportFailures -= 1;
      throw const ClientTransportFailure();
    }
    lastTags = List<String>.from(tags);
    lastText = text;
  }

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    commitCalls += 1;
    commitKeys.add(idempotencyKey);
    events.add('commit');
    if (commitTransportFailures > 0) {
      commitTransportFailures -= 1;
      throw const ClientTransportFailure();
    }
  }

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'reason-actor',
      accessToken: 'reason-token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async => reasonCase;

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    return const [];
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    events.add('reveal');
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 42,
      confidence: 'MEDIUM',
      values: {'A': 0.55, 'B': 0.45},
    );
  }

  @override
  Future<String> startSession(String caseId) async => 'reason-session';
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

Future<MemoryDecisionDraftStore> pumpReasonCase(
  WidgetTester tester,
  ReasonFakeRepository repository,
) async {
  final draftStore = MemoryDecisionDraftStore();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(draftStore),
      ],
      child: const KefeApp(initialLocation: '/case/$reasonCaseId'),
    ),
  );
  await tester.pumpAndSettle();
  return draftStore;
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

Future<void> tapCommit(WidgetTester tester) async {
  await tapVisible(tester, find.byKey(const ValueKey('commit-button')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('blank private reason stays optional and is not submitted', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ReasonFakeRepository();
    await pumpReasonCase(tester, repository);

    await tapVisible(tester, find.byKey(const ValueKey('option-A')));
    expect(
      const KefeStrings(Locale('tr', 'TR')).reasonHelper,
      contains('diğer kullanıcılara gösterilmez'),
    );

    await tapCommit(tester);

    expect(repository.reasonCalls, 0);
    expect(repository.commitCalls, 1);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
  });

  testWidgets('schema-driven private reason is persisted and synced before Commit', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ReasonFakeRepository();
    final draftStore = await pumpReasonCase(tester, repository);

    await tapVisible(tester, find.byKey(const ValueKey('option-A')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-FAIRNESS')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-NEED')));
    final reasonText = find.byKey(const ValueKey('reason-text'));
    await tester.scrollUntilVisible(
      reasonText,
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.enterText(reasonText, 'Adalet ve ihtiyaç birlikte etkili oldu.');
    await tester.pumpAndSettle();

    final localDraft = draftStore.draftFor(reasonCaseId)!;
    expect(localDraft.reasonTags, containsAll(['FAIRNESS', 'NEED']));
    expect(localDraft.reasonText, 'Adalet ve ihtiyaç birlikte etkili oldu.');

    await tapCommit(tester);

    expect(repository.lastTags, ['FAIRNESS', 'NEED']);
    expect(repository.lastText, 'Adalet ve ihtiyaç birlikte etkili oldu.');
    expect(repository.events, ['answer', 'reason', 'commit', 'reveal']);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
    expect(draftStore.draftFor(reasonCaseId), isNull);
  });

  testWidgets('reason tag selection respects the CaseVersion max_tags policy', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ReasonFakeRepository();
    final draftStore = await pumpReasonCase(tester, repository);

    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-FAIRNESS')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-NEED')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-RESPONSIBILITY')));
    await tester.pumpAndSettle();

    final tags = draftStore.draftFor(reasonCaseId)!.reasonTags;
    expect(tags, hasLength(2));
    expect(tags, containsAll(['FAIRNESS', 'NEED']));
    expect(tags, isNot(contains('RESPONSIBILITY')));
  });

  testWidgets('sync failure stays pre-Commit and safely retries draft plus reason', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ReasonFakeRepository()..reasonTransportFailures = 1;
    final draftStore = await pumpReasonCase(tester, repository);

    await tapVisible(tester, find.byKey(const ValueKey('option-A')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-FAIRNESS')));
    await tapCommit(tester);

    final pending = draftStore.draftFor(reasonCaseId)!;
    expect(pending.phase, DecisionDraftPhase.syncPending);
    expect(repository.commitCalls, 0);

    final idempotencyKey = pending.commitIdempotencyKey;
    await tapCommit(tester);

    expect(repository.answerCalls, 2);
    expect(repository.reasonCalls, 2);
    expect(repository.commitCalls, 1);
    expect(repository.commitKeys.single, idempotencyKey);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
  });

  testWidgets('uncertain Commit retries only Commit with the same key', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = ReasonFakeRepository()..commitTransportFailures = 1;
    final draftStore = await pumpReasonCase(tester, repository);

    await tapVisible(tester, find.byKey(const ValueKey('option-B')));
    await tapVisible(tester, find.byKey(const ValueKey('reason-tag-RESPONSIBILITY')));
    await tapCommit(tester);

    expect(draftStore.draftFor(reasonCaseId)?.phase, DecisionDraftPhase.commitPending);
    expect(repository.answerCalls, 1);
    expect(repository.reasonCalls, 1);
    expect(repository.commitCalls, 1);
    final key = repository.commitKeys.single;

    await tapCommit(tester);

    expect(repository.answerCalls, 1);
    expect(repository.reasonCalls, 1);
    expect(repository.commitCalls, 2);
    expect(repository.commitKeys, [key, key]);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

import 'support/flow_runtime_fixture.dart';

const perspectiveCaseId = 'cccccccc-1111-4111-8111-cccccccccccc';
const perspectiveQuestionId = 'perspective-choice';

const perspectiveCase = DecisionCase(
  id: perspectiveCaseId,
  versionId: 'perspective-version-1',
  title: 'Perspektif testi',
  summary: 'Reveal sonrasında farklı bakışları gör.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: perspectiveQuestionId,
      prompt: 'Hangisini seçerdin?',
      responseType: 'SINGLE_CHOICE',
      options: ['A', 'B'],
      responseSchema: {
        'reason': {
          'tags': ['FAIRNESS'],
          'max_tags': 1,
          'text_enabled': true,
          'text_max_length': 120,
        },
      },
    ),
  ],
);

class PerspectiveFakeRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository, PerspectiveRepository {
  PerspectiveFakeRepository() {
    flowCaseVersionId = perspectiveCase.versionId;
  }

  int answerCalls = 0;
  int reasonCalls = 0;
  int commitCalls = 0;
  int revealCalls = 0;
  int perspectiveCalls = 0;
  int perspectiveTransportFailures = 0;

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
  }) async {
    reasonCalls += 1;
  }

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
      actorId: 'perspective-actor',
      accessToken: 'perspective-token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async => perspectiveCase;

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    return const [];
  }

  @override
  Future<String> startSession(String caseId) async => 'perspective-session';

  @override
  Future<RevealResult> reveal(String sessionId) async {
    revealCalls += 1;
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 128,
      confidence: 'HIGH',
      values: {'A': 0.52, 'B': 0.48},
    );
  }

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) async {
    perspectiveCalls += 1;
    if (perspectiveTransportFailures > 0) {
      perspectiveTransportFailures -= 1;
      throw const ClientTransportFailure();
    }
    return PerspectiveResult(
      sessionId: sessionId,
      caseVersionId: perspectiveCase.versionId,
      cards: const [
        PerspectiveCard(
          id: 'near',
          slot: PerspectiveSlot.near,
          body: 'Sana yakın ama aynı olmayan bir gerekçe.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'opposing',
          slot: PerspectiveSlot.opposing,
          body: 'Karşı yöndeki en güçlü gerekçelerden biri.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'bridge',
          slot: PerspectiveSlot.bridge,
          body: 'İki taraf arasında ortak bir değer noktası.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'context',
          slot: PerspectiveSlot.alternativeContext,
          body: 'Bağlam değiştiğinde kararın neden değişebileceği.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
      ],
      methodology: PerspectiveMethodology(
        mode: 'DEGRADED_CURATED',
        sampleKind: 'CURATED_FALLBACK',
        sampleSize: 4,
        generatedAt: DateTime.utc(2026, 7, 27),
        provenanceNote: 'Düşük riskli editoryal fallback seti.',
      ),
    );
  }
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

Future<void> pumpPerspectiveCase(
  WidgetTester tester,
  PerspectiveFakeRepository repository,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
      ],
      child: const KefeApp(initialLocation: '/case/$perspectiveCaseId'),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> makeVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pump(const Duration(milliseconds: 100));
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await makeVisible(tester, finder);
  await tester.tap(finder);
  await tester.pump();
}

Future<void> commitChoice(WidgetTester tester) async {
  await tester.tap(find.byKey(const ValueKey('option-A')));
  await tester.pump();
  await tapVisible(tester, find.byKey(const ValueKey('commit-button')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Perspective is not requested or visible before Commit', (tester) async {
    useTurkishLocale(tester);
    final repository = PerspectiveFakeRepository();
    await pumpPerspectiveCase(tester, repository);

    expect(repository.perspectiveCalls, 0);
    expect(find.byKey(const ValueKey('perspective-section')), findsNothing);
  });

  testWidgets('Reveal automatically continues into bounded curated Perspective', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = PerspectiveFakeRepository();
    await pumpPerspectiveCase(tester, repository);
    await commitChoice(tester);

    expect(repository.commitCalls, 1);
    expect(repository.revealCalls, 1);
    expect(repository.perspectiveCalls, 1);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);

    final section = find.byKey(const ValueKey('perspective-section'));
    await makeVisible(tester, section);
    expect(section, findsOneWidget);
    expect(find.byKey(const ValueKey('perspective-curated-note')), findsOneWidget);
    expect(find.byKey(const ValueKey('perspective-card-near')), findsOneWidget);
    expect(find.byKey(const ValueKey('perspective-card-opposing')), findsOneWidget);
    expect(find.byKey(const ValueKey('perspective-card-bridge')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('perspective-card-alternativeContext')),
      findsOneWidget,
    );
  });

  testWidgets('pending private reason is labeled without becoming a Perspective source', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = PerspectiveFakeRepository();
    await pumpPerspectiveCase(tester, repository);

    await tester.tap(find.byKey(const ValueKey('option-A')));
    final reason = find.byKey(const ValueKey('reason-text'));
    await makeVisible(tester, reason);
    await tester.enterText(reason, 'Bu yalnızca benim özel gerekçem.');
    await tester.pump();
    await tapVisible(tester, find.byKey(const ValueKey('commit-button')));
    await tester.pumpAndSettle();

    expect(repository.reasonCalls, 1);
    final pending = find.byKey(const ValueKey('reason-pending-moderation'));
    await makeVisible(tester, pending);
    expect(pending, findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('perspective-section')),
        matching: find.textContaining('Bu yalnızca benim özel gerekçem.'),
      ),
      findsNothing,
    );
  });

  testWidgets('Perspective retry never replays answer reason Commit or Reveal', (
    tester,
  ) async {
    useTurkishLocale(tester);
    final repository = PerspectiveFakeRepository()..perspectiveTransportFailures = 1;
    await pumpPerspectiveCase(tester, repository);
    await commitChoice(tester);

    expect(repository.answerCalls, 1);
    expect(repository.commitCalls, 1);
    expect(repository.revealCalls, 1);
    expect(repository.perspectiveCalls, 1);

    final retry = find.byKey(const ValueKey('perspective-retry'));
    await makeVisible(tester, retry);
    await tester.tap(retry);
    await tester.pumpAndSettle();

    expect(repository.answerCalls, 1);
    expect(repository.reasonCalls, 0);
    expect(repository.commitCalls, 1);
    expect(repository.revealCalls, 1);
    expect(repository.perspectiveCalls, 2);
    expect(find.byKey(const ValueKey('perspective-card-opposing')), findsOneWidget);
  });
}

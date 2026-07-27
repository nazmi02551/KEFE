import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

const typedCaseId = 'aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa';
const choiceQuestionId = 'choice-question';
const confidenceQuestionId = 'confidence-question';

class TypedQuestionRepository implements DecisionRepository {
  final Map<String, Object> submitted = {};

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {
    submitted[questionId] = value;
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
  }) async {}

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    return GuestCredential(
      actorId: 'actor-typed',
      accessToken: 'token',
      expiresAt: DateTime.utc(2026, 8),
    );
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async {
    return const DecisionCase(
      id: typedCaseId,
      versionId: 'typed-version-1',
      title: 'Typed questions',
      summary: 'Choice plus confidence.',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: choiceQuestionId,
          prompt: 'Choose',
          responseType: 'SINGLE_CHOICE',
          options: ['A', 'B'],
        ),
        DecisionQuestion(
          id: confidenceQuestionId,
          prompt: 'Confidence',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 5, 'step': 1},
        ),
      ],
    );
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    return const [];
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    return const RevealResult(
      layer: 'TRUSTED',
      sampleSize: 10,
      confidence: 'LOW',
      values: {'A': 0.6, 'B': 0.4},
    );
  }

  @override
  Future<String> startSession(String caseId) async => 'typed-session';
}

Future<void> pumpTypedCase(
  WidgetTester tester,
  TypedQuestionRepository repository,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
      ],
      child: const KefeApp(initialLocation: '/case/$typedCaseId'),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('required choice enables Commit while Confidence stays optional', (
    tester,
  ) async {
    final repository = TypedQuestionRepository();
    await pumpTypedCase(tester, repository);

    final commit = find.byKey(const ValueKey('commit-button'));
    expect(tester.widget<FilledButton>(commit).onPressed, isNull);

    await tester.tap(find.byKey(const ValueKey('option-A')));
    await tester.pump();
    expect(tester.widget<FilledButton>(commit).onPressed, isNotNull);
  });

  testWidgets('Confidence is rendered from schema and submitted with the choice', (
    tester,
  ) async {
    final repository = TypedQuestionRepository();
    await pumpTypedCase(tester, repository);

    expect(
      find.byKey(const ValueKey('confidence-$confidenceQuestionId-4')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('option-B')));
    await tester.pump();
    await tester.tap(
      find.byKey(const ValueKey('confidence-$confidenceQuestionId-4')),
    );
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('commit-button')));
    await tester.pumpAndSettle();

    expect(repository.submitted[choiceQuestionId], 'B');
    expect(repository.submitted[confidenceQuestionId], 4);
    expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
  });
}
